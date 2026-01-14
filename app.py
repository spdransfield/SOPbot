### streamlit UI ###
import streamlit as st
from src.rag_pipeline import SOPRAGPipeline

# Page config
st.set_page_config(
    page_title="CRE SOP Knowledge Assistant",
    page_icon="📚",
    layout="wide"
)


## init ##
@st.cache_resource
def load_pipeline():
    return SOPRAGPipeline()


pipeline = load_pipeline()

## UI ##
st.title("📚 CRE SOP Knowledge Assistant")
st.markdown("Ask questions about Clinical Research Enterprise Standard Operating Procedures")

## side ##
with st.sidebar:
    st.header("About")
    st.info(
        "This system uses Azure AI Search and OpenAI to answer questions "
        "about CRE SOPs using Retrieval-Augmented Generation (RAG)."
    )

    st.header("Settings")
    top_k = st.slider("Number of sources to retrieve", 1, 5, 3)
    show_sources = st.checkbox("Show source documents", value=True)

## main ##
query = st.text_input(
    "Enter your question:",
    placeholder="e.g., What is the patient parking procedure at CH20?"
)

if st.button("Search", type="primary") or query:
    if query:
        with st.spinner("Searching SOPs..."):
            result = pipeline.query(query, top_k=top_k)

        # answer #
        st.subheader("Answer")
        st.write(result["answer"])

        # sources #
        if show_sources and result["sources"]:
            st.subheader("Sources")
            for i, source in enumerate(result["sources"], 1):
                st.markdown(f"{i}. {source}")

        # Display retrieved content  #
        if show_sources:
            with st.expander("View retrieved document excerpts"):
                for i, doc in enumerate(result["retrieved_docs"], 1):
                    st.markdown(f"**Document {i}** (Score: {doc['score']:.3f})")
                    st.text(doc["content"][:500] + "...")
                    st.markdown("---")

##  Example queries ##
st.subheader("Example Questions")
examples = [
    "What is the parking procedure for patients at CH20?",
    "How should informed consent be obtained remotely?",
    "What should I do during a sponsor audit?",
    "What are the UAB addresses for clinical research?",
    "Who is responsible for fiscal reporting?"
]

cols = st.columns(len(examples))
for col, example in zip(cols, examples):
    if col.button(example[:30] + "...", key=example):
        st.rerun()