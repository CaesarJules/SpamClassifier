import streamlit as st
import pandas as pd
import numpy as np
import requests
from plotly.offline import iplot
import plotly.graph_objs as go
import plotly.express as px
from pandas.io.json import json_normalize
from streamlit.script_runner import RerunException, StopException
import time
import os
import matplotlib.pyplot as plt
from functions import *

#Backend API IP address
url="http://x.y.z.1996:8000/api/status/"
#Get the current file's directory
path = os.path.dirname(__file__)
filepath = os.path.join(path, 'data/sample_annotated.csv')
#Create logo filepath
logo = os.path.join(path, 'data/logo.png')
st.set_page_config(page_title='Spam Detector', page_icon = logo, layout = 'wide', initial_sidebar_state = 'auto')

def test_url_availability(url):
    try:
        site_ping = requests.head(url)
        if site_ping.status_code < 400:
            return True
    except Exception:
        return False

fig = go.Figure()
st.title("Spam Detector")
st.text("")
st.text("")
st.text("")
#---------------------------------#
# About
expander_bar = st.expander("About")
expander_bar.markdown("""
##### This app is a reviews' *spam classifier*.
* **EDA and Model Development Details :** [Github](https://github.com/CaesarJules/SpamClassifier).
* **Sample dataset source :** [TensorFlow Datasets](https://www.tensorflow.org/datasets/catalog/amazon_us_reviews#amazon_us_reviewspc_v1_00).
* **Python libraries used:** streamlit, pandas, numpy, requests, plotly, time, os, matplotlib.
""")

st.set_option('deprecation.showfileUploaderEncoding', False)

st.text("")
st.text("")

col2, col3 = st.columns((2,1))

sample = col2.empty()
sample.selectbox(label = "", options=["", "Amazon PC reviews sample"], key="sample_id")
disable_sidebar = False
if st.session_state["sample_id"]!="":
    disable_sidebar = True
st.sidebar.write("# Customer Product Review(s)")
st.sidebar.text("")
st.sidebar.text("")

def refresh_app(session, request_queue):
    del session["fl_id"]
    del session["txt_id"]
    del session["sample_id"]
    raise RerunException(request_queue.RerunData(None))

with st.sidebar:
    with st.form("myform", clear_on_submit=True):
        single_review = st.text_area(label="Please enter below a product review:", key="txt_id", disabled=disable_sidebar)
        st.write("# Or")
        uploaded_file = st.file_uploader(label="Upload your input reviews CSV file", key="fl_id",
        type=["csv"], disabled=disable_sidebar)
        st.warning("Note: Products reviews must be stored in a column called *review*")
        submit = st.form_submit_button(label="Submit")

    if submit:
        temp = st.empty()
        if test_url_availability(url) == False:
            col2.error("# Sorry, the server is currently unreachable. In the meantime, please use the sample dataset above.")
            time.sleep(3)
            refresh_app(st.session_state, st.script_request_queue)

        if uploaded_file!=None:
            valid_data = "review" in list(pd.read_csv(uploaded_file, nrows=0).columns)
            if valid_data == False:
                temp.error('There must be a review column in your dataset!')
                time.sleep(1)
                refresh_app(st.session_state, st.script_request_queue)
            else:
                temp.success('Submitted')
        elif len(single_review.strip()) > 0:
            sample.empty()
            temp.success('Submitted')   
        else:
            temp.error('You must have at least one review!')
        time.sleep(1)
        temp.empty()

st.sidebar.markdown("***")

if st.sidebar.button('Refresh Page'):
    refresh_app(st.session_state, st.script_request_queue)

if uploaded_file != None or st.session_state["sample_id"]!="":
    filter_unverified = col3.checkbox('Filter out Unverified Reviews')
    input_df = pd.DataFrame()
    with st.spinner('Fetching Results ...'):
        if st.session_state["sample_id"] != "":
            df = pd.read_csv(filepath, low_memory=False)
            if test_url_availability(url) == False:
                data = pd.DataFrame(df)
            else:
                sample_data = get_results(df.drop(columns=['status']), url)
                data = pd.DataFrame(sample_data)
        elif uploaded_file != None:
            uploaded_file.seek(0)    
            input_df = pd.read_csv(uploaded_file, low_memory=False)
            uploaded_data = get_results(input_df, url)
            data = pd.DataFrame(uploaded_data)
        else:
            pass

        sample.empty()
        df = pd.DataFrame(data)
      
        if filter_unverified == False:
            total_result = df[["status", "verified"]].value_counts(sort=False)
            colors = total_result.to_frame().reset_index().status.map({"Real":'rgb(153, 255, 153)',"Spam":'rgb(255, 153, 153)'}).to_list()
            display_updated_layout(df, total_result, colors, col2, col3, fig)
                    
        elif filter_unverified == True:
            df = df[df['verified']=="verified"].reset_index(drop=True)
            total_result = df[["status", "verified"]].value_counts(sort=False)
            colors = total_result.to_frame().reset_index().status.map({"Real":'rgb(153, 255, 153)',"Spam":'rgb(255, 153, 153)'}).to_list()
            display_updated_layout(df, total_result, colors, col2, col3, fig)
                    
        else:
            pass
       
elif len(single_review.strip())>0:
    result = None
    if test_url_availability(url) == True:
        sample.empty()
        body = {'review': single_review}
        r = requests.post(url, data = body)
        result = r.json()["review_status"]

    if result=="Real":
        st.success("## Awesome, that's a real review! &nbsp;😃")
    elif result=="Spam":
        st.warning("## Sorry, you have a spam review! &nbsp;😔")
    else:
        col2.error("# Sorry, the server is currently unreachable. In the meantime, please use the sample dataset above.")
        time.sleep(3)
        refresh_app(st.session_state, st.script_request_queue)
    
else:
    col2.subheader(" ⬅ Please enter product reviews, or use one of the sample dataset(s) provided above")

    


