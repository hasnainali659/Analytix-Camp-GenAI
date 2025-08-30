import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.output_parsers import StrOutputParser
from neo4j import GraphDatabase

load_dotenv()

def relationship_to_string(relationship):
    """Convert a Neo4j Relationship into a string like:
       (:Entity {name: "Hasnain Ali Poonja"})-[:HAS_EDUCATION]->(:Entity {name: "NUST SMME"})
    """
    try:
        node1, node2 = relationship.nodes
        
        label1 = list(node1.labels)[0] if node1.labels else ""
        label2 = list(node2.labels)[0] if node2.labels else ""
        
        name1 = node1.get("name", "Unknown")
        name2 = node2.get("name", "Unknown")
        
        rel_type = relationship.type
        
        return f'(:{label1} {{name: "{name1}"}})-[:{rel_type}]->(:{label2} {{name: "{name2}"}})'
    except Exception as e:
        print(f"Error in relationship_to_string: {str(e)}")
        return "Unknown relationship"

def init_neo4j_connection():
    """Initialize Neo4j connection with error handling"""
    try:
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI", ""),
            username=os.getenv("NEO4J_USERNAME", ""),
            password=os.getenv("NEO4J_PASSWORD", "")
        )
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", ""),
            auth=(os.getenv("NEO4J_USERNAME", ""), os.getenv("NEO4J_PASSWORD", ""))
        )
        
        return graph, driver
    except Exception as e:
        print(f"Failed to initialize Neo4j connection: {str(e)}")
        return None, None

def get_schema(graph):
    """Get schema with error handling"""
    try:
        return graph.get_schema() if graph else ""
    except Exception as e:
        print(f"APOC error retrieving schema: {str(e)}")
        return ""

def get_all_nodes_and_relationships(driver, file_names_list=None):
    """Get all nodes and relationships with robust error handling"""
    if not driver:
        return [], []
        
    nodes_list = []
    relationships_list = []
    
    try:
        with driver.session() as session:
            base_query = """
                MATCH (n:Entity)
                OPTIONAL MATCH (n)-[r]-(m:Entity)
                RETURN DISTINCT n, r, m
            """
            
            result = session.run(base_query)
            for record in result:
                if record.get("n") and record["n"].get("name"):
                    nodes_list.append(record["n"]["name"])
                if record.get("m") and record["m"].get("name"):
                    nodes_list.append(record["m"]["name"])
                if record.get("r"):
                    rel_str = relationship_to_string(record["r"])
                    relationships_list.append(rel_str)
        
        return list(set(nodes_list)), list(set(relationships_list))
    except Exception as e:
        print(f"Error in get_all_nodes_and_relationships: {str(e)}")
        return [], []

def get_relationships_for_node(driver, node_name):
    """Get relationships for node with error handling"""
    if not driver or not node_name:
        return [], []
        
    try:
        query = """
            MATCH (n {name: $node_name})-[r]-(m)
            RETURN n, r, m
        """
        with driver.session() as session:
            result = session.run(query, node_name=node_name)
            
            records = []
            relationships = []
            for record in result:
                records.append({
                    "node": record.get("n", {}),
                    "relationship": record.get("r", {}),
                    "connected_node": record.get("m", {})
                })
                if record.get("r"):
                    relationships.append(record["r"].type)
            return records, relationships
    except Exception as e:
        print(f"Error in get_relationships_for_node: {str(e)}")
        return [], []
    
def extract_main_node_chain(query, nodes):
    """Extract main node with error handling"""
    if not query or not nodes:
        return ""
        
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        prompt = PromptTemplate(
            template=""" You are a highly skilled assistant that specializes in extracting the main node from a query.
            You are given a query and a list of all nodes in the graph database.
            You need to extract the main node from the query.
            The main node is the node that is most relevant to the query.
            
            Note: Only return the name of the node.
            
            Query: {query}
            List of all nodes: {nodes}
            
            Main node:
            """
        )
        
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"query": query, "nodes": nodes})
    except Exception as e:
        print(f"Error in extract_main_node_chain: {str(e)}")
        return ""
    
def rephrase_query_chain(query, nodes, relationships):
    """Rephrase query with error handling"""
    if not query:
        return None
        
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        prompt = PromptTemplate(
            template=""" You are a highly skilled assistant that specializes in rephrasing user queries using the list of nodes and the 
            list of relationships in the graph database. 

            The rephrased query should include the exact node and the relevant relationship of the node from the list of nodes and the list of relationships.

            List of nodes: {nodes}
            List of relationships: {relationships}
            Query: {query}

            Rephrased Query:
            """
        )
        
        chain = prompt | llm
        return chain.invoke({"nodes": nodes, "relationships": relationships, "query": query})
    except Exception as e:
        print(f"Error in rephrase_query_chain: {str(e)}")
        return None

def init_qa_chain(graph, schema):
    """Initialize QA chain with error handling"""
    try:
        template = """
        Task: Generate a Cypher statement to query the graph database.
        You will be given a rephrased query.
        Generate a cypher statement to answer the rephrased query.

        Instructions:
        1. Search for nodes and their relationships
        2. Return relevant information about the queried entities
        3. Don't restrict to specific labels, search across all nodes
        4. Use CONTAINS or other fuzzy matching when appropriate

        schema:
        {schema}

        Note: Focus on finding relevant information rather than exact matches.

        Rephrased Query: {query}

        Cypher Statement:
        """ 

        question_prompt = PromptTemplate(
            template=template, 
            input_variables=["schema", "query", "file_names_list"] 
        )

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        return GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=question_prompt,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True
        )
    except Exception as e:
        print(f"Error initializing QA chain: {str(e)}")
        return None

def direct_node_search(driver, search_term):
    """Perform direct node search with error handling"""
    if not driver or not search_term:
        return []
        
    try:
        search_query = """
            MATCH (n:Entity)
            WHERE n.name CONTAINS $search_term
            OPTIONAL MATCH (n)-[r]-(m:Entity)
            RETURN n, r, m
        """
        
        with driver.session() as session:
            search_result = session.run(search_query, {"search_term": search_term.lower()})
            return [record for record in search_result]
    except Exception as e:
        print(f"Error in direct_node_search: {str(e)}")
        return []

def format_search_results(records):
    """Format search results with error handling"""
    if not records:
        return {}
        
    try:
        formatted_result = {
            "nodes": [],
            "relationships": []
        }
        
        for record in records:
            if record.get("n") and record["n"].get("name"):
                formatted_result["nodes"].append(record["n"]["name"])
            if record.get("r"):
                formatted_result["relationships"].append(record["r"].type)
                
        return formatted_result
    except Exception as e:
        print(f"Error formatting search results: {str(e)}")
        return {}

def process_query(question, file_names_list=None):
    """Handle the complete query processing workflow with robust error handling"""
    if not question:
        return {"error": "No question provided"}
        
    try:
        graph, driver = init_neo4j_connection()
        if not graph or not driver:
            return {"error": "Failed to connect to database"}
            
        schema = get_schema(graph)
        qa = init_qa_chain(graph, schema)
        if not qa:
            return {"error": "Failed to initialize QA chain"}
            
        if file_names_list is None:
            file_names_list = []
            
        nodes_list, relationships_list = get_all_nodes_and_relationships(driver, file_names_list)
        
        print(f"Processing question: {question}")
        print(f"Available nodes: {nodes_list}")
        print(f"Available relationships: {relationships_list}")
        
        rephrased = rephrase_query_chain(question, nodes_list, relationships_list)
        if not rephrased or not hasattr(rephrased, 'content') or not rephrased.content:
            return {"error": "Failed to rephrase query", "status": "error"}
            
        print(f"Rephrased query: {rephrased.content}")
        
        try:
            result = qa.invoke({
                "query": rephrased.content,
                "file_names_list": file_names_list
            })
            
            if result and "result" in result and result["result"] != "I don't know the answer.":
                return {
                    "status": "success",
                    "rephrased_query": rephrased.content,
                    "result": result["result"]
                }
        except Exception as e:
            print(f"QA chain error: {str(e)}")
        
        records = direct_node_search(driver, question)
        if records:
            formatted_result = format_search_results(records)
            if formatted_result:
                return {
                    "status": "success",
                    "rephrased_query": rephrased.content,
                    "result": formatted_result
                }
        
        return {
            "status": "partial",
            "rephrased_query": rephrased.content,
            "result": "No specific information found for this query."
        }
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        return {"error": str(e), "status": "error"}
    
if __name__ == "__main__":
    question = "What are the common skills of the candidates?"
    process_query(question)