import streamlit as st

from main import build_index, build_chat_engine

IMPACT_DOCUMENT_LINK = "https://docs.google.com/document/d/19YTAi7l2OzadvUeBm_xfWLBbcm8HaTZb7XBlbVV7LoU/edit?usp=sharing"


@st.cache_resource
def index():
    return build_index()


def energy_message(count: int):
    energy_use = round(count * 0.1, 2)
    query_text = "query" if count == 1 else "queries"
    st.caption(
        f"You have made {count} {query_text}, equivalent to microwaving food for {energy_use} seconds.\n"
    )


def chatbot():
    st.title("Chat With Sustainability")

    model_options = ["llama-3.1-8b-instant"]
    if "model_name" not in st.session_state:
        st.session_state.model_name = model_options[0]

    with st.expander("BEFORE YOU BEGIN CHATTING...", expanded=True):
        st.caption(
            f"""
            Regarding AI energy usage, there is often a focus on the energy used in model 
            training. Today, however, inference - not training - represents an increasing 
            majority of AI energy demands, with estimates suggesting 80 to 90 percent of 
            computing power for AI is used for inference. 

            With every query, an AI chatbot consumes a certain amount of electricity, water, 
            and carbon. Model size plays a massive role with respect to this energy consumption! 
            Thus, our chatbot intentionally uses a smaller, energy-efficient model (LLaMA 3.1 8B), 
            where each query is approximately equivalent to running a microwave for a tenth 
            of a second.

            While using a lightweight model can reduce the environmental footprint of our 
            chatbot, and the impact of a single query appears low, it is still important 
            to see the bigger picture on the environmental cost that AI carries. 
                    
            For more information, please visit the following [document]({IMPACT_DOCUMENT_LINK}).
        """
        )

    model_name = st.text_input("Model", value=st.session_state.model_name)

    if (
        "chat_engine" not in st.session_state
        or st.session_state.model_name != model_name
    ):
        st.session_state.chat_engine = build_chat_engine(index(), model=model_name)
        st.session_state.model_name = model_name

    chat_engine = st.session_state.chat_engine

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Clear"):
        st.session_state.messages = []

    assistant_count = 0
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                assistant_count += 1
                energy_message(assistant_count)

    if prompt := st.chat_input("Type your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            stream = chat_engine.stream_chat(prompt)
            response = st.write_stream(stream.response_gen)
            energy_message(assistant_count + 1)

        st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    chatbot()


if __name__ == "__main__":
    main()
