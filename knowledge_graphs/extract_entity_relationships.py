import os
from typing import Union
import PyPDF2

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, Field

from neo4j import GraphDatabase
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

class DocClass(Enum):
    RESUME = "resume"
    SCIENCE_ARTICLE = "science_article"
    TECHNICAL_DOCUMENT = "technical_document"

class Neo4jConnection:
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        
        """
        Initialize Neo4j connection
        
        Args:
            uri (str): Neo4j URI (e.g., "bolt://localhost:7687")
            username (str): Neo4j username
            password (str): Neo4j password
            database (str): Database name (default is "neo4j")
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            print("Connection to Neo4j DB successful")
        except Exception as e:
            print(f"Failed to connect to Neo4j DB: {e}")
    
    def close(self):
        """
        Close the Neo4j driver connection
        """
        if self.driver is not None:
            self.driver.close()
            print("Neo4j connection closed")
    
    def query(self, query: str, parameters: dict = None) -> Union[list, None]:
        """
        Execute a Cypher query
        
        Args:
            query (str): Cypher query
            parameters (dict): Query parameters (optional)
            
        Returns:
            list: Query results or None if error occurs
        """
        assert self.driver is not None, "Driver not initialized!"
        session = None
        response = None
        
        try:
            session = self.driver.session(database=self.database)
            response = list(session.run(query, parameters or {}))
        except Exception as e:
            print(f"Query failed: {e}")
        finally:
            if session is not None:
                session.close()
        
        return response

    def write_transaction(self, query: str, parameters: dict = None):
        """
        Execute a write transaction
        
        Args:
            query (str): Cypher query for writing data
            parameters (dict): Query parameters (optional)
        """
        assert self.driver is not None, "Driver not initialized!"
        session = None
        
        try:
            session = self.driver.session(database=self.database)
            session.execute_write(
                lambda tx: tx.run(query, parameters or {})
            )
        except Exception as e:
            print(f"Write transaction failed: {e}")
        finally:
            if session is not None:
                session.close()

class ContentSchema(BaseModel):
    entities: list[str] = Field(default=[], description="The list of entities in the resume")
    relationships: list[str] = Field(default=[], description="The list of relationships between entities in the resume")
    cypher_queries: list[str] = Field(default=[], description="The list of cypher queries to create the knowledge graph")
    root_entity_name: str = Field(default='', description="The name of the root entity. For e.g 'Bob Smith', 'Robotics Article'")

def extract_text_from_pdf(pdf_path: str) -> str:
    full_text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            full_text += page.extract_text()
    return full_text
    
def get_all_nodes_and_relationships():
    query = """MATCH (n) OPTIONAL MATCH (n)-[r]-() RETURN DISTINCT n, r"""
    
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    
    print("Connecting to Neo4j at:", NEO4J_URI)
    
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    nodes = []
    relationships = []
    
    try:
        with driver.session() as session:
            result = session.run(query)

            for record in result:
                node = record["n"]
                rel = record["r"]
                
                # Safely get node properties
                if node and hasattr(node, '_properties'):
                    node_name = node._properties.get('name')
                    if node_name:  # Only append if name exists
                        nodes.append(node_name)
                
                # Safely get relationship type
                if rel is not None and hasattr(rel, 'type'):
                    relationships.append(rel.type)
    except Exception as e:
        print(f"Error querying Neo4j: {str(e)}")
        raise
    finally:
        driver.close()
    
    # Remove duplicates and None values
    nodes = list(set([n for n in nodes if n]))
    relationships = list(set([r for r in relationships if r]))
    
    print(f"Found {len(nodes)} nodes and {len(relationships)} relationships")
    return nodes, relationships

    
def process_document(pdf_path: str, doc_class: str):
    try:
        full_text = extract_text_from_pdf(pdf_path)
        
        try:
            all_nodes, all_relationships = get_all_nodes_and_relationships()
        except Exception as e:
            print(f"Warning: Could not fetch existing nodes/relationships: {str(e)}")
            all_nodes, all_relationships = [], []
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        parser = PydanticOutputParser(pydantic_object=ContentSchema)
        
        template = """
        IMPORTANT: Ensure your output is valid JSON with all keys and string values enclosed in double quotes.
        You are a document parser. Your primary objective is to analyze the provided document and extract key components to construct
        a knowledge graph. You will be given the following inputs:
        
        - A document text (which could be a resume, science article, or technical document).
        - The document class (which indicates the type or category of the document).
        - A list of all previously extracted relationships (all_relationships). For first document, all_relationships will be empty.

        Your task is to extract:
        1. **Entities:** Key names, institutions, concepts, topics, skills, locations, etc.
        2. **Relationships:** The connections between these entities. When determining a relationship, check the provided all_relationships list. 
        If a similar relationship already exists (even if represented with different synonyms), use the existing relationship name.  
        - *For example:*  
            - **HAS_AUTHORED** and **AUTHORED_BY** are considered the same.  
            - **HAS_CONTRIBUTED** and **AUTHORED_BY** are considered the same.  
            - So, if **HAS_AUTHORED** is already in the all_relationships list, do not create **AUTHORED_BY**; instead, use **HAS_AUTHORED**.  
            - Similarly, if **HAS_CONTRIBUTED** exists, do not generate **AUTHORED_BY**; use **HAS_CONTRIBUTED**.
        3. **Cypher Queries:** Generate Cypher queries that logically connect the extracted entities. Each query should:
        - Create or merge nodes for each entity.
        - Create relationships connecting the nodes, ensuring every entity is linked to the designated root entity.
        - Be written in a clear, easy-to-understand manner.
        4. **Root Entity Name:** Identify and assign the main or most representative entity of the document as the root node. Every other entity should be connected directly or indirectly to this root.

        **Important Guidelines:**
        - **Comprehensiveness:** Extract as many entities and relationships as possible. Ensure no relevant piece of information is omitted.
        - **Context Sensitivity:** 
        - For resumes, focus on aspects like Person Name, Education (degrees or institutions), Work Experience (companies and job titles), Skills, Location, Certifications, Awards, etc.
        - For science articles, look for Topic, Authors, Affiliations, Contributions, Novelty, Research methods, Methodology, Results, and Conclusion.
        - For technical documents, capture the Topic, Technical Details, How it Works, Applications, and Impact.
        - **Connection Logic:**  

        - Every node must be connected to the root entity node via an appropriate relationship.
        - For example, if "NED University" is mentioned, it should be connected with a relationship related to education or institution, not one meant for contributions.  
        - Similarly, "Karachi" should be connected with a relationship related to location or residence rather than an institution-related relationship.

        **Output Format:**
        Use the following JSON-like structure as a guide. Do not alter the double curly braces {{ }} as they are required by the Langchain format.
        {{
            'entities': [...],
            'relationships': [...],
            'cypher_queries': [...],
            'root_entity_name': '...'
        }}

        **Detailed Examples:**

        ----------------------------------
        Example 1: Resume Document
        ----------------------------------
        Document:
        "My name is Alice Johnson. I have a Bachelor of Science in Computer Science from the University of Texas. I worked at IBM as a Data Scientist. My skill set includes Python, Machine Learning, and Data Analysis."

        Expected Output:
        {{
            'entities': ['Alice Johnson', 'University of Texas', 'IBM', 'Data Scientist', 'Python', 'Machine Learning', 'Data Analysis'],
            'relationships': ['HAS_EDUCATION', 'HAS_EXPERIENCE', 'HAS_SKILLS'],
            'cypher_queries': [
                "MERGE (person:Entity {{name: 'Alice Johnson'}}) RETURN person",
                "MERGE (school:Entity {{name: 'University of Texas'}}) RETURN school",
                "MERGE (company:Entity {{name: 'IBM'}}) RETURN company",
                "MERGE (role:Entity {{name: 'Data Scientist'}}) RETURN role",
                "MERGE (skill1:Entity {{name: 'Python'}}) RETURN skill1",
                "MERGE (skill2:Entity {{name: 'Machine Learning'}}) RETURN skill2",
                "MERGE (skill3:Entity {{name: 'Data Analysis'}}) RETURN skill3",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (school:Entity {{name: 'University of Texas'}}) MERGE (person)-[:HAS_EDUCATION]->(school)",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (company:Entity {{name: 'IBM'}}) MERGE (person)-[:HAS_EXPERIENCE]->(company)",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (role:Entity {{name: 'Data Scientist'}}) MERGE (person)-[:HAS_EXPERIENCE]->(role)",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (skill1:Entity {{name: 'Python'}}) MERGE (person)-[:HAS_SKILLS]->(skill1)",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (skill2:Entity {{name: 'Machine Learning'}}) MERGE (person)-[:HAS_SKILLS]->(skill2)",
                "MATCH (person:Entity {{name: 'Alice Johnson'}}), (skill3:Entity {{name: 'Data Analysis'}}) MERGE (person)-[:HAS_SKILLS]->(skill3)"
            ],
            'root_entity_name': 'Alice Johnson'
        }}

        ----------------------------------
        Example 2: Resume with Additional Details
        ----------------------------------
        Resume:
        "I am Bob Smith, living in San Francisco. I graduated with a Master's in Data Science from Stanford University, and I have experience at Google as a Machine Learning Engineer. I am proficient in Python, C++, and SQL. I also received the 'Innovator Award' for my contributions to AI research."

        Expected Output:
        {{
            'entities': ['Bob Smith', 'San Francisco', 'Stanford University', 'Google', 'Machine Learning Engineer', 'Python', 'C++', 'SQL', 'Innovator Award', 'AI Research'],
            'relationships': ['LIVES_IN', 'HAS_EDUCATION', 'HAS_EXPERIENCE', 'HAS_SKILLS', 'HAS_AWARDS', 'HAS_RESEARCH'],
            'cypher_queries': [
                "MERGE (person:Entity {{name: 'Bob Smith'}}) RETURN person",
                "MERGE (city:Entity {{name: 'San Francisco'}}) RETURN city",
                "MERGE (university:Entity {{name: 'Stanford University'}}) RETURN university",
                "MERGE (company:Entity {{name: 'Google'}}) RETURN company",
                "MERGE (role:Entity {{name: 'Machine Learning Engineer'}}) RETURN role",
                "MERGE (skill1:Entity {{name: 'Python'}}) RETURN skill1",
                "MERGE (skill2:Entity {{name: 'C++'}}) RETURN skill2",
                "MERGE (skill3:Entity {{name: 'SQL'}}) RETURN skill3",
                "MERGE (award:Entity {{name: 'Innovator Award'}}) RETURN award",
                "MERGE (research:Entity {{name: 'AI Research'}}) RETURN research",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (city:Entity {{name: 'San Francisco'}}) MERGE (person)-[:LIVES_IN]->(city)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (university:Entity {{name: 'Stanford University'}}) MERGE (person)-[:HAS_EDUCATION]->(university)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (company:Entity {{name: 'Google'}}) MERGE (person)-[:HAS_EXPERIENCE]->(company)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (role:Entity {{name: 'Machine Learning Engineer'}}) MERGE (person)-[:HAS_EXPERIENCE]->(role)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (skill1:Entity {{name: 'Python'}}) MERGE (person)-[:HAS_SKILLS]->(skill1)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (skill2:Entity {{name: 'C++'}}) MERGE (person)-[:HAS_SKILLS]->(skill2)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (skill3:Entity {{name: 'SQL'}}) MERGE (person)-[:HAS_SKILLS]->(skill3)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (award:Entity {{name: 'Innovator Award'}}) MERGE (person)-[:HAS_AWARDS]->(award)",
                "MATCH (person:Entity {{name: 'Bob Smith'}}), (research:Entity {{name: 'AI Research'}}) MERGE (person)-[:HAS_RESEARCH]->(research)"
            ],
            'root_entity_name': 'Bob Smith'
        }}

        ----------------------------------
        Example 3: Science Article
        ----------------------------------
        Document:
        "The article discusses the latest advancements in robotics, including the development of a new robotic arm that can perform complex tasks. The research highlights experimental methodologies and significant improvements in precision."

        Expected Output:
        {{
            'entities': ['Robotics', 'Robotic Arm', 'Complex Tasks', 'Experimental Methodologies', 'Precision Improvements'],
            'relationships': ['HAS_ADVANCES', 'HAS_DEVELOPMENT', 'HAS_METHODOLOGY', 'HAS_RESULTS'],
            'cypher_queries': [
                "MERGE (article:Entity {{name: 'Robotics Article'}}) RETURN article",
                "MERGE (advancement:Entity {{name: 'Robotics'}}) RETURN advancement",
                "MERGE (arm:Entity {{name: 'Robotic Arm'}}) RETURN arm",
                "MERGE (task:Entity {{name: 'Complex Tasks'}}) RETURN task",
                "MERGE (method:Entity {{name: 'Experimental Methodologies'}}) RETURN method",
                "MERGE (result:Entity {{name: 'Precision Improvements'}}) RETURN result",
                "MATCH (article:Entity {{name: 'Robotics Article'}}), (advancement:Entity {{name: 'Robotics'}}) MERGE (article)-[:HAS_ADVANCES]->(advancement)",
                "MATCH (article:Entity {{name: 'Robotics Article'}}), (arm:Entity {{name: 'Robotic Arm'}}) MERGE (article)-[:HAS_DEVELOPMENT]->(arm)",
                "MATCH (article:Entity {{name: 'Robotics Article'}}), (method:Entity {{name: 'Experimental Methodologies'}}) MERGE (article)-[:HAS_METHODOLOGY]->(method)",
                "MATCH (article:Entity {{name: 'Robotics Article'}}), (result:Entity {{name: 'Precision Improvements'}}) MERGE (article)-[:HAS_RESULTS]->(result)"
            ],
            'root_entity_name': 'Robotics'
        }}

        ----------------------------------
        Example 4: Technical Document
        ----------------------------------
        Document:
        "This Handbook is a comprehensive guide to the latest advancements in AI, including the development of a new AI model that can perform complex tasks. AI is the future of the world, influencing industries and transforming societies."

        Expected Output:
        {{
            'entities': ['AI', 'AI Model', 'Complex Tasks', 'Future of the World', 'Industries', 'Societies'],
            'relationships': ['HAS_ADVANCES', 'HAS_DEVELOPMENT', 'HAS_IMPACT', 'HAS_APPLICATION'],
            'cypher_queries': [
                "MERGE (document:Entity {{name: 'Handbook'}}) RETURN document",
                "MERGE (topic:Entity {{name: 'AI'}}) RETURN topic",
                "MERGE (model:Entity {{name: 'AI Model'}}) RETURN model",
                "MERGE (task:Entity {{name: 'Complex Tasks'}}) RETURN task",
                "MERGE (impact:Entity {{name: 'Future of the World'}}) RETURN impact",
                "MERGE (industry:Entity {{name: 'Industries'}}) RETURN industry",
                "MERGE (society:Entity {{name: 'Societies'}}) RETURN society",
                "MATCH (document:Entity {{name: 'Handbook'}}), (topic:Entity {{name: 'AI'}}) MERGE (document)-[:HAS_ADVANCES]->(topic)",
                "MATCH (document:Entity {{name: 'Handbook'}}), (model:Entity {{name: 'AI Model'}}) MERGE (document)-[:HAS_DEVELOPMENT]->(model)",
                "MATCH (document:Entity {{name: 'Handbook'}}), (task:Entity {{name: 'Complex Tasks'}}) MERGE (document)-[:HAS_DEVELOPMENT]->(task)",
                "MATCH (document:Entity {{name: 'Handbook'}}), (impact:Entity {{name: 'Future of the World'}}) MERGE (document)-[:HAS_IMPACT]->(impact)",
                "MATCH (document:Entity {{name: 'Handbook'}}), (industry:Entity {{name: 'Industries'}}) MERGE (document)-[:HAS_APPLICATION]->(industry)",
                "MATCH (document:Entity {{name: 'Handbook'}}), (society:Entity {{name: 'Societies'}}) MERGE (document)-[:HAS_APPLICATION]->(society)"
            ],
            'root_entity_name': 'AI'
        }}

        ----------------------------------
        Example 5: Mixed Technical and Research Document
        ----------------------------------
        Document:
        "Dr. Emily Clark presents a whitepaper on quantum computing. The document outlines the principles of quantum mechanics, details the design of a quantum processor, and discusses the potential impact on cybersecurity and data encryption. It also covers experimental results from recent trials."

        Expected Output:
        {{
            'entities': ['Dr. Emily Clark', 'Quantum Computing', 'Quantum Mechanics', 'Quantum Processor', 'Cybersecurity', 'Data Encryption', 'Experimental Results'],
            'relationships': ['HAS_AUTHORED', 'HAS_TOPICS', 'HAS_DEVELOPMENT', 'HAS_IMPACT', 'HAS_RESULTS'],
            'cypher_queries': [
                "MERGE (document:Entity {{name: 'Whitepaper on Quantum Computing'}}) RETURN document",
                "MERGE (author:Entity {{name: 'Dr. Emily Clark'}}) RETURN author",
                "MERGE (topic:Entity {{name: 'Quantum Computing'}}) RETURN topic",
                "MERGE (mechanics:Entity {{name: 'Quantum Mechanics'}}) RETURN mechanics",
                "MERGE (processor:Entity {{name: 'Quantum Processor'}}) RETURN processor",
                "MERGE (cyber:Entity {{name: 'Cybersecurity'}}) RETURN cyber",
                "MERGE (encryption:Entity {{name: 'Data Encryption'}}) RETURN encryption",
                "MERGE (results:Entity {{name: 'Experimental Results'}}) RETURN results",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (author:Entity {{name: 'Dr. Emily Clark'}}) MERGE (document)-[:HAS_AUTHORED]->(author)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (topic:Entity {{name: 'Quantum Computing'}}) MERGE (document)-[:HAS_TOPICS]->(topic)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (mechanics:Entity {{name: 'Quantum Mechanics'}}) MERGE (document)-[:HAS_TOPICS]->(mechanics)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (processor:Entity {{name: 'Quantum Processor'}}) MERGE (document)-[:HAS_DEVELOPMENT]->(processor)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (cyber:Entity {{name: 'Cybersecurity'}}) MERGE (document)-[:HAS_IMPACT]->(cyber)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (encryption:Entity {{name: 'Data Encryption'}}) MERGE (document)-[:HAS_IMPACT]->(encryption)",
                "MATCH (document:Entity {{name: 'Whitepaper on Quantum Computing'}}), (results:Entity {{name: 'Experimental Results'}}) MERGE (document)-[:HAS_RESULTS]->(results)"
            ],
            'root_entity_name': 'Quantum Computing'
        }}

        ----------------------------------
        Instructions for Processing the Input:
        Now, using the same approach and output format structure shown in the examples above, parse the following inputs:

        - **Document:** {text}
        - **Document Class:** {doc_class}
        - **All Relationships:** {all_relationships}


        Your output should comprehensively list all relevant entities, determine the appropriate relationships (reusing existing relationship names when applicable), and generate clear, logically connected cypher queries that integrate every extracted entity with the chosen root entity. Make sure no entity is left unconnected.

        Remember:  
        - Use clear and descriptive relationship names that reflect the nature of the connection (e.g., HAS_EDUCATION, LIVES_IN, HAS_EXPERIENCE, HAS_ADVANCES, HAS_DEVELOPMENT, HAS_IMPACT, etc.).
        """


        
        prompt = PromptTemplate(template=template)
        chain = prompt | llm
        
        response = chain.invoke({"text": full_text, "doc_class": doc_class, "all_relationships": all_relationships})
        response_content = response.content if hasattr(response, 'content') else response


        # try:
        #     parsed_response = parser.parse(response_content)
        # except OutputParserException:
        #     new_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
        #     parsed_response = new_parser.parse(response_content)
        
        try:
            parsed_response = parser.parse(response_content)
        except OutputParserException:
            fixed_response = response_content.replace("'", "\"")
            parsed_response = parser.parse(fixed_response)
        
        entities = parsed_response.entities
        relationships = parsed_response.relationships
        cypher_queries = parsed_response.cypher_queries
        root_entity_name = parsed_response.root_entity_name
        
        print("Root entity name extracted:", root_entity_name)
        print("Entities extracted:", entities)
        print("Relationships extracted:", relationships)
        print("Cypher queries extracted:", cypher_queries)

        NEO4J_URI = os.getenv('NEO4J_URI')
        NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
        NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

        neo4j_connection = Neo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

        query = f"""MERGE (r:{doc_class} {{name: '{doc_class.lower()}'}}) RETURN r"""
        neo4j_connection.write_transaction(query)

        file_name = os.path.basename(pdf_path)
        
        file_query = """MERGE (f:File {name: $file_name}) RETURN f"""
        file_query_params = {'file_name': file_name}
        neo4j_connection.write_transaction(file_query, file_query_params)

        belongs_query = f"""
            MATCH (r:{doc_class} {{ name: '{doc_class.lower()}' }}), (f:File {{ name: $file_name }})
            MERGE (f)-[:BELONGS_TO]->(r) 
            RETURN r, f
        """
        neo4j_connection.write_transaction(belongs_query, file_query_params)

        for cypher_query in cypher_queries:
            neo4j_connection.write_transaction(cypher_query)

        root_entity_query = """
            MATCH (b { name: $root_entity_name }), (f { name: $file_name })
            MERGE (b)-[:HAS_FILE]->(f)
            RETURN b, f
        """
        root_entity_query_params = {
            'root_entity_name': root_entity_name,
            'file_name': file_name
        }
        neo4j_connection.write_transaction(root_entity_query, root_entity_query_params)

        print(f"Finished processing {file_name} into the Neo4j graph.")

    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise

if __name__ == "__main__":
    pdf_path = "docs/Khawer-CV.pdf" 
    doc_class = DocClass.RESUME.value
    process_document(pdf_path, doc_class)