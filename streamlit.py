import streamlit as st

from main import build_index, build_chat_engine


@st.cache_resource
def index():
    return build_index()


def chatbot():
    st.title("Chat With Sustainability")

    model_options = ["llama-3.1-8b-instant"]
    if "model_idx" not in st.session_state:
        st.session_state.model_name = model_options[0]

    model_name = st.text_input("Model", value=st.session_state.model_name)
    st.session_state.model_name = model_name

    if (
        "chat_engine" not in st.session_state
        or st.session_state.model_idx != model_options.index(model_name)
    ):
        st.session_state.chat_engine = build_chat_engine(index(), model=model_name)
        st.session_state.model_idx = model_options.index(model_name)

    chat_engine = st.session_state.chat_engine

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Clear"):
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            stream = chat_engine.stream_chat(prompt)
            response = st.write_stream(stream.response_gen)

        st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    chatbot()


if __name__ == "__main__":
    main()
