import streamlit as st
import random

from main import build_index, build_chat_engine

IMPACT_DOCUMENT_LINK = "https://docs.google.com/document/d/19YTAi7l2OzadvUeBm_xfWLBbcm8HaTZb7XBlbVV7LoU/edit?usp=sharing"

# Energy comparison metrics - each equivalent to around 0.03 Wh
ENERGY_COMPARISONS = [
    {
        "emoji": "🍕", 
        "template": "microwaving food for {value} seconds", 
        "factor": 0.1},
    {
        "emoji": "💡",
        "template": "powering a 60W light bulb for {value} seconds",
        "factor": 1.7,
    },
    {
        "emoji": "🚲", 
        "template": "powering an e-bike for {value} feet", 
        "factor": 6},
    {
        "emoji": "🔍", 
        "template": "making {value} Google searches", 
        "factor": 0.1
    },
    {
        "emoji": "📱",
        "template": "charging a smartphone for {value} seconds",
        "factor": 22.8
    }
]


@st.cache_resource
def index():
    return build_index()


def energy_message(count: int, comparison_index: int):
    """Display energy usage message with a random comparison metric."""
    query_text = "query" if count == 1 else "queries"

    # Get the comparison metric for this query
    comparison = ENERGY_COMPARISONS[comparison_index]

    # Calculate the value based on the comparison's factor
    value = round(count * comparison["factor"], 2)

    # Format the message with emoji and description
    message = comparison["template"].format(value=value)

    st.caption(
        f"{comparison['emoji']} You have made {count} {query_text}, equivalent to {message}.\n"
    )


def sidebar_analogy_text(latest_comparison, scaled_query_count):
    """
    Convert the scaled number of queries into the same metric the user sees
    in the main UI — using the metric's template AND scientific notation.
    """
    if not latest_comparison:
        return None

    factor = latest_comparison["factor"]

    # Compute the scaled value like the main metric does
    raw_value = scaled_query_count * factor

    # Format in scientific notation for readability
    sci_value = f"{raw_value:.2e}"
    mantissa, exponent = sci_value.split("e")
    exponent = int(exponent)
    formatted_value = f"{mantissa}×10^{exponent}"

    # Apply the template
    analogy_text = latest_comparison["template"].format(value=formatted_value)

    return analogy_text


def chatbot():
    st.title("Chat With Sustainability")

    model_options = ["llama-3.1-8b-instant"]
    if "model_name" not in st.session_state:
        st.session_state.model_name = model_options[0]

    # Initialize query_count
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0

    # Initialize comparison_metrics list to store which comparison was used for each query
    if "comparison_metrics" not in st.session_state:
        st.session_state.comparison_metrics = []

    if st.session_state.comparison_metrics:
        latest_index = st.session_state.comparison_metrics[-1]
        latest_comparison = ENERGY_COMPARISONS[latest_index]
    else:
        latest_comparison = None

    with st.sidebar:
        if st.session_state.comparison_metrics:
            latest_index = st.session_state.comparison_metrics[-1]
            latest_comparison = ENERGY_COMPARISONS[latest_index]
        else:
            latest_comparison = None

        # Calculate scaled query count 
        scaled_query_count = st.session_state.query_count * 120_000_000

        dynamic_analogy = sidebar_analogy_text(latest_comparison, scaled_query_count)

        st.title("FOOD FOR THOUGHT...")
        st.write(
            f"""
            Perhaps you consider the energy used across this conversation small, 
            negligible even. However, it is important to zoom out and see the 
            bigger picture.

            First of all, our use of LLaMA 3.1 8B (a SLM with below 10B parameters) 
            dramatically decreases the energy used. If we were to use OpenAI's complex 
            reasoning model o3, which has billions of parameters, one query requires 
            around 21 Wh of energy, 700x higher than that required by LLaMA 3.1 8B!

            Additionally, large language models, such as ChatGPT and Claude, serve tens of millions 
            of people every day. As of November 2025, ChatGPT alone sees roughly 120 
            million users daily. If we were to scale your energy use by that number, 
            it would be equivalent to **{dynamic_analogy}**!
            """
        )

    with st.expander("BEFORE YOU BEGIN CHATTING...", expanded=True):
        st.caption(
            f"""
            Regarding AI energy usage, there is often a focus on the energy used in model 
            training. Today, however, inference - not training - represents an increasing 
            majority of AI energy demands, with estimates suggesting 80 to 90 percent of 
            computing power for AI is used for inference. 

            With every query, an AI chatbot consumes electricity and water while also generating
            carbon emissions. Model size plays a massive role with respect to this energy consumption! 
            Thus, our chatbot intentionally uses a smaller, energy-efficient model (LLaMA 3.1 8B), 
            where each query requires around 0.03 Wh of energy. This is approximately 
            equivalent to running a microwave for 0.1 seconds, or riding an e-bike for 6 ft.

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
        st.session_state.query_count = 0
        st.session_state.comparison_metrics = []
        st.rerun()

    assistant_index = 0
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                comparison_index = st.session_state.comparison_metrics[assistant_index]
                energy_message(assistant_index + 1, comparison_index)
                assistant_index += 1

    if prompt := st.chat_input("Type your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            stream = chat_engine.stream_chat(prompt)
            response = st.write_stream(stream.response_gen)

            st.session_state.query_count += 1

            # Randomly select a comparison metric and store it
            comparison_index = random.randint(0, len(ENERGY_COMPARISONS) - 1)
            st.session_state.comparison_metrics.append(comparison_index)

            energy_message(st.session_state.query_count, comparison_index)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


def main():
    chatbot()


if __name__ == "__main__":
    main()
