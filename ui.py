import streamlit as st
from flask import Flask
import pandas as pd
import time
from dateutil.parser import parse as parse_datetime, ParserError
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://nitesh8527:Nitesh8527@cluster0.bxxtr.mongodb.net/github-webhook?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['github-webhook']
collection = db['events']


def format_time(ts):
    if not ts:
        return "No timestamp"
    try:
        dt = parse_datetime(ts)
        return dt.strftime("%d %B %Y - %I:%M %p UTC")
    except ParserError:
        return "Invalid timestamp"


st.title("Live MongoDB Events Stream")

# Track seen event IDs to avoid duplicates
if "event_ids" not in st.session_state:
    st.session_state.event_ids = set()

# DataFrame to hold all events as a single "Event" column
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Event"])

placeholder = st.empty()

while True:
    events_cursor = collection.find().sort("timestamp", 1)
    new_rows = []

    for event in events_cursor:
        _id = str(event.get("_id"))
        if _id not in st.session_state.event_ids:
            author = event.get("author", "Unknown")
            action = event.get("action", "").upper()
            from_branch = event.get("from_branch", "")
            to_branch = event.get("to_branch", "")
            timestamp = event.get("timestamp", "")

            formatted_time = format_time(timestamp)

            if action == "PUSH":
                description = f'"{author}" pushed to "{to_branch}"'
            elif action == "PULL_REQUEST":
                description = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}"'
            elif action == "MERGE":
                description = f'"{author}" merged branch "{from_branch}" to "{to_branch}"'
            else:
                description = f'"{author}" performed "{action}"'

            event_text = f"{description} on {formatted_time}"

            new_rows.append({"Event": event_text})
            st.session_state.event_ids.add(_id)

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)

    placeholder.dataframe(st.session_state.df, use_container_width=True)

    time.sleep(15)


