import streamlit as st


def write_streaming_response(response):
    placeholder = st.empty()
    message = ""
    for chunk in response:
        delta = chunk.choices[0]["delta"]
        if "content" in delta:
            message += delta["content"]
            placeholder.markdown(message + "▌")
        else:
            break
    placeholder.markdown(message)
    return message
