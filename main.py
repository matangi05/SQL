import os
import sqlite3
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import sqlalchemy
from sqlalchemy import create_engine, inspect
from urllib.parse import quote_plus
from sqlalchemy import text

def get_db_connection(db_url):
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

def get_schema_info(engine):
    inspector = inspect(engine)
    schema_info = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema_info[table_name] = [col['name'] for col in columns]
    return schema_info

def get_query(query, schema_info):
    schema_str = "\n".join([f"Table {table}: {', '.join(columns)}" 
                           for table, columns in schema_info.items()])
    
    prompt = ChatPromptTemplate.from_template("""
                    You are an expert in converting English questions to SQL query!
                    Here is the database schema:
                    {schema}
                    
                    Convert the following question in English to a valid SQL Query: {query}
                    The SQL query should work with the provided schema.
                    No preamble, only valid SQL please.
                    Quote all table/column names using double quotes if needed
                    Do not include ```sql or ``` in the output.
                    """)
    
    model = "llama3-8b-8192"
    llm = ChatGroq(
        groq_api_key = os.environ.get("groq_api_key"), 
        model_name = model) 
    chain = prompt | llm | StrOutputParser()
    sqlquery = chain.invoke({"query": query, "schema": schema_str})
    return text(sqlquery)

def get_data(engine, sql):
    try:
        with engine.connect() as conn:
            result = conn.execute(sql)
            return result.fetchall()
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return []

def main():
    st.set_page_config(page_title='SQL Retriever')
    st.header("Talk to your Database!")
    
    db_url = st.text_input("Enter your database connection URL:", 
                          help="Example: postgresql://user:password@localhost:5432/dbname")
    
    if db_url:
        engine = get_db_connection(db_url)
        if engine:
            schema_info = get_schema_info(engine)
            
            st.subheader("Database Schema")
            for table, columns in schema_info.items():
                st.write(f"Table: {table}")
                st.write(f"Columns: {', '.join(columns)}")
            
            query = st.text_input("Enter your query: ")
            submit = st.button("Enter")

            if submit:
                sql = get_query(query, schema_info)
                data = get_data(engine, sql)
                st.subheader(f"Retrieving results from the database for the query: [{sql}]")
                for row in data:
                    st.write(row)

if __name__ == "__main__":
    main()
