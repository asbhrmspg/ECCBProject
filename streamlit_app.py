import streamlit as st

st.title("RUGRATS")
st.write(
    """
    🐀 664 Rug Rats was formed with the intention of providing knowledge on
    finance and business through much simpler means. Information so essential to our
    daily lives have become ridiculously difficult to access due to how broad
    "Financial Education" really is. But fret no longer! 
    \n\n\nWe have built
    RUGRat, an AI Agent that will assist users with learning these concepts!
    """
)



if st.button("Visit our AI Agent, RUGRat! ➡️"):
    st.switch_page("pages/app.py")
