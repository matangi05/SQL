import os
import sqlite3
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

def get_query(query):
    prompt = ChatPromptTemplate.from_template("""
                    You are an expert in converting English questions to SQL query!
                    The SQL database has the name STUDENT and has the following columns - NAME, COURSE, 
                    SECTION and MARKS. For example, 
                    Example 1 - How many entries of records are present?, 
                        the SQL command will be something like this SELECT COUNT(*) FROM STUDENT;
                    Example 2 - Tell me all the students studying in Data Science COURSE?, 
                        the SQL command will be something like this SELECT * FROM STUDENT 
                        where COURSE="Data Science"; 
                    also the sql code should not have ``` in beginning or end and sql word in output.
                    Now convert the following question in English to a valid SQL Query: {query}. 
                    No preamble, only valid SQL please
                                                       """)
    model = "llama3-8b-8192"
    llm = ChatGroq(
        groq_api_key = os.environ.get("groq_api_key"), 
        model_name = model) 
    chain = prompt | llm | StrOutputParser()
    sqlquery = chain.invoke({"query": query})
    return sqlquery

def get_data(sql):
    db = "student.db"
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()

def main():
    st.set_page_config(page_title='SQL Retriever')
    st.header("Talk to your Database!")
    query = st.text_input("Enter your query: ")
    submit=st.button("Enter")

    if submit:
        sql = get_query(query)
        data = get_data(sql)
        st.subheader(f"Retrieving results from the database for the query: [{sql}]")
        for row in data:
            st.write(row)

if __name__ == "__main__":
    main()
