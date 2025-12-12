import streamlit as st
import random

from main import build_index, build_chat_engine

IMPACT_DOCUMENT_LINK = "https://docs.google.com/document/d/19YTAi7l2OzadvUeBm_xfWLBbcm8HaTZb7XBlbVV7LoU/edit?usp=sharing"

# Energy comparison metrics - each equivalent to ~0.1 second of microwave usage
ENERGY_COMPARISONS = [
    {"emoji": "🍕", "template": "microwaving food for {value} seconds", "factor": 0.1},
    {
        "emoji": "🔦",
        "template": "running an LED bulb for {value} seconds",
        "factor": 1.5,
    },
    {
        "emoji": "📱",
        "template": "charging a smartphone for {value} seconds",
        "factor": 0.08,
    },
    {
        "emoji": "💡",
        "template": "running an incandescent bulb for {value} seconds",
        "factor": 0.25,
    },
    {
        "emoji": "🌳",
        "template": "what a small plant absorbs in {value} seconds of sunlight",
        "factor": 15,
    },
    {"emoji": "🚲", "template": "powering an e-bike for {value} meters", "factor": 0.5},
    {"emoji": "☕", "template": "heating {value}ml of water by 1°C", "factor": 1.0},
    {
        "emoji": "🧠",
        "template": "your brain operating for {value} second",
        "factor": 1.0,
    },
    {"emoji": "🎵", "template": "streaming music for {value} seconds", "factor": 0.3},
    {
        "emoji": "📺",
        "template": "running a modern TV for {value} seconds",
        "factor": 0.15,
    },
    {"emoji": "⚡", "template": "powering a laptop for {value} seconds", "factor": 0.1},
    {
        "emoji": "🏃",
        "template": "energy burned taking {value} steps while walking",
        "factor": 0.15,
    },
    {"emoji": "💾", "template": "writing to an SSD {value} times", "factor": 1000},
    {
        "emoji": "🎮",
        "template": "running a gaming console (idle) for {value} seconds",
        "factor": 0.12,
    },
    {"emoji": "📧", "template": "sending {value} emails", "factor": 15},
    {
        "emoji": "🌡️",
        "template": "running a smart thermostat for {value} seconds",
        "factor": 5,
    },
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


def chatbot():
    st.title("Chat With Sustainability")

    model_options = ["llama-3.1-8b-instant"]
    if "model_name" not in st.session_state:
        st.session_state.model_name = model_options[0]

    # Initialize energy_use in session state
    if "energy_use" not in st.session_state:
        st.session_state.energy_use = 0

    # Initialize comparison_metrics list to store which comparison was used for each query
    if "comparison_metrics" not in st.session_state:
        st.session_state.comparison_metrics = []

    with st.sidebar:
        # Calculate scaled energy use from session state
        scaled_energy = st.session_state.energy_use * 120_000_000

        if scaled_energy < 60:
            time_str = f"{scaled_energy:.1f} seconds"
        elif scaled_energy < 3600:
            minutes = scaled_energy / 60
            time_str = f"{minutes:.1f} minutes"
        elif scaled_energy < 86400:
            hours = scaled_energy / 3600
            time_str = f"{hours:.1f} hours"
        else:
            days = scaled_energy / 86400
            time_str = f"{days:.1f} days"

        st.title("FOOD FOR THOUGHT...")
        st.write(
            f"""
            Perhaps you consider the energy used across this conversation small, 
            negligible even. However, it is important to zoom out and see the 
            bigger picture.

            First of all, our use of LLaMA 3.1 8B dramatically decreases the energy used. 
            If we were to use OpenAI's complex reasoning model o3, which has billions
            of parameters, one query would be equivalent to running a microwave for
            76 seconds, which is more than 700x higher than that for LLaMA 3.1 8B!

            Large language models, such as ChatGPT and Claude, serve tens of millions 
            of people every day. As of November 2025, ChatGPT alone sees roughly 120 
            million users daily. If we were to scale your energy use by that number, 
            it would be equivalent to running a microwave for **{time_str}**! 

            (By then, whatever you were heating up would have progressed well past well-done, 
            likely turning into smoldering, charred black mass…)
            """
        )

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
        st.session_state.energy_use = 0
        st.session_state.comparison_metrics = []
        st.rerun()

    assistant_count = 0
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                assistant_count += 1
                # Use the stored comparison index for this query
                comparison_index = st.session_state.comparison_metrics[
                    assistant_count - 1
                ]
                energy_message(assistant_count, comparison_index)

    if prompt := st.chat_input("Type your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            stream = chat_engine.stream_chat(prompt)
            response = st.write_stream(stream.response_gen)

            # Update energy use in session state
            assistant_count += 1
            st.session_state.energy_use = round(assistant_count * 0.1, 2)

            # Randomly select a comparison metric and store it
            comparison_index = random.randint(0, len(ENERGY_COMPARISONS) - 1)
            st.session_state.comparison_metrics.append(comparison_index)

            energy_message(assistant_count, comparison_index)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


def main():
    chatbot()


if __name__ == "__main__":
    main()
