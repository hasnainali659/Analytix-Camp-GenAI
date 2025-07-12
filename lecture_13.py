import streamlit as st
import numpy as np
import pandas as pd

st.title("Hello Streamlit")
st.write("This is a simple text")

df = pd.DataFrame({
    'first column': [1,2,3,4,5],
    'second column': [10,20,30,40,50]
})

st.write("Here is the dataframe")
st.write(df)

chart_data = pd.DataFrame(
    np.random.randn(20,3), columns=['a', 'b', 'c']
)

st.line_chart(chart_data)

name = st.text_input("Enter your name: ")

if name:
    st.write(f"Hello {name}")

age = st.slider("Select your age: ")

if age:
    st.write(f"your age is {age}")

options = ["python", "Java", "C++"]
choice = st.selectbox("choose your favourite language: ", options)

st.write(f"You selected {choice}")

uploaded_file = st.file_uploader("choose a csv file", type='csv')

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)