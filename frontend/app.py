import streamlit as st
import sys
from pathlib import Path

# add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.api_client import get_api_client

# page config
st.set_page_config(
    page_title="Heart&Mind | AI-Powered Recommendations",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# load custom CSS
def load_css():
    with open("styles/custom.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css()
except:
    pass  # CSS file not found, continue without styling

# initialize API client
api = get_api_client()

# session state initialization
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = 1
if 'personality' not in st.session_state:
    st.session_state.personality = 'friendly'


def main():
    """Main app"""
    
    # check API health
    if not api.health_check():
        st.error("⚠️ **Backend API is not running!**")
        st.info("Start the backend server first: `cd backend && python -m app.main`")
        st.stop()
    
    # header with gradient
    st.markdown("""
        <h1 class="gradient-text">
            Heart&Mind
        </h1>
        <p style="color: #8b8b8b; font-size: 1.2rem; margin-top: -20px;">
            Neural Experience Understanding System
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # sidebar - user selection
    with st.sidebar:
        st.markdown("### 👤 Select User")
        
        users = api.get_users()
        if users:
            user_options = {f"{u['name']} ({u['email']})": u['id'] for u in users}
            selected_user_name = st.selectbox(
                "Choose a user:",
                options=list(user_options.keys()),
                key="user_selector"
            )
            st.session_state.selected_user = user_options[selected_user_name]
        else:
            st.error("No users found!")
            st.stop()
        
        st.markdown("---")
        
        # personality selector
        st.markdown("### 🎭 Explanation Style")
        
        personalities = {
            '🤗 Friendly': 'friendly',
            '🎓 Expert': 'expert',
            '📖 Storyteller': 'storyteller',
            '⚡ Minimalist': 'minimalist'
        }
        
        selected_personality = st.radio(
            "Choose explanation style:",
            options=list(personalities.keys()),
            key="personality_selector"
        )
        st.session_state.personality = personalities[selected_personality]
        
        st.markdown("---")
        
        # quick stats
        st.markdown("### 📊 Quick Stats")
        analytics = api.get_user_analytics(st.session_state.selected_user)
        
        if analytics and 'total_interactions' in analytics:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Interactions", analytics.get('total_interactions', 0))
            with col2:
                st.metric("Purchases", analytics.get('total_purchases', 0))
            
            if analytics.get('favorite_category'):
                st.info(f"💜 Favorite: **{analytics['favorite_category']}**")
    
    # main content tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Recommendations", "📊 Analytics", "🛍️ Browse Products"])
    
    with tab1:
        show_recommendations()
    
    with tab2:
        show_analytics()
    
    with tab3:
        show_products()


def show_recommendations():
    """Show personalized recommendations"""
    st.markdown("## ✨ Your Personalized Recommendations")
    
    user_id = st.session_state.selected_user
    personality = st.session_state.personality
    
    # settings
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Based on your behavior and preferences**")
    with col2:
        num_recs = st.slider("Number", 5, 20, 10, key="num_recs")
    
    # get recommendations
    with st.spinner("🔮 Generating recommendations..."):
        recs_data = api.get_recommendations(
            user_id=user_id,
            n=num_recs,
            personality=personality,
            include_explanations=True
        )
    
    recommendations = recs_data.get('recommendations', [])
    
    if not recommendations:
        st.warning("No recommendations available yet. Start browsing products!")
        return
    
    # display recommendations
    for i, rec in enumerate(recommendations):
        product = rec['product']
        explanation = rec.get('explanation', 'No explanation available')
        source = rec.get('source', 'unknown')
        score = rec.get('score', 0)
        
        # create card
        with st.container():
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # product image placeholder
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        height: 150px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 3rem;
                    ">
                        {product['category'][:2].upper()}
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # product details
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"### {product['name']}")
                with col_b:
                    st.markdown(f"<h3 style='text-align: right; color: #667eea;'>${product['price']}</h3>", unsafe_allow_html=True)
                
                # tags
                tags_html = ""
                for tag in product.get('tags', []):
                    tags_html += f'<span class="tag">{tag}</span>'
                
                # source badge
                if 'serendipity' in source:
                    tags_html += '<span class="serendipity-badge">✨ Discovery</span>'
                
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.markdown(f"**Category:** {product['category']} • **Rating:** ⭐ {product['rating']}/5.0")
                
                # AI Explanation
                st.markdown(f"""
                    <div style="
                        background: rgba(102, 126, 234, 0.1);
                        border-left: 3px solid #667eea;
                        padding: 12px;
                        border-radius: 8px;
                        margin-top: 12px;
                    ">
                        <strong>💬 Why this for you:</strong><br>
                        {explanation}
                    </div>
                """, unsafe_allow_html=True)
                
                # action buttons
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                with col_btn1:
                    if st.button("👁️ View", key=f"view_{i}"):
                        api.track_interaction(user_id, product['id'], 'view')
                        st.success("Viewed!")
                with col_btn2:
                    if st.button("🛒 Cart", key=f"cart_{i}"):
                        api.track_interaction(user_id, product['id'], 'cart')
                        st.success("Added to cart!")
                with col_btn3:
                    if st.button("💜 Wishlist", key=f"wish_{i}"):
                        api.track_interaction(user_id, product['id'], 'wishlist')
                        st.success("Added to wishlist!")
                with col_btn4:
                    if st.button("✅ Buy", key=f"buy_{i}"):
                        api.track_interaction(user_id, product['id'], 'purchase')
                        st.success("Purchased!")
                        st.balloons()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)


def show_analytics():
    """Show user analytics"""
    st.markdown("## 📊 Your Shopping Insights")
    
    user_id = st.session_state.selected_user
    analytics = api.get_user_analytics(user_id)
    
    if not analytics or 'total_interactions' not in analytics:
        st.info("No analytics data available yet. Start shopping!")
        return
    
    # metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Interactions",
            value=analytics.get('total_interactions', 0)
        )
    
    with col2:
        st.metric(
            label="Purchases",
            value=analytics.get('total_purchases', 0)
        )
    
    with col3:
        st.metric(
            label="Total Spent",
            value=f"${analytics.get('total_spent', 0):.2f}"
        )
    
    with col4:
        fav_cat = analytics.get('favorite_category', 'N/A')
        st.metric(
            label="Favorite Category",
            value=fav_cat
        )
    
    st.markdown("---")
    
    # categories explored
    if analytics.get('categories_explored'):
        st.markdown("### 🎯 Categories You've Explored")
        
        categories = analytics['categories_explored']
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analytics['total_interactions']) * 100
            st.markdown(f"""
                <div style="margin: 8px 0;">
                    <strong>{category}</strong>: {count} interactions ({percentage:.1f}%)
                    <div style="
                        background: rgba(102, 126, 234, 0.2);
                        height: 8px;
                        border-radius: 4px;
                        overflow: hidden;
                    ">
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            height: 100%;
                            width: {percentage}%;
                        "></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)


def show_products():
    """Browse all products"""
    st.markdown("## 🛍️ Browse Products")
    
    # category filter
    categories = ['All'] + api.get_categories()
    selected_category = st.selectbox("Filter by category:", categories)
    
    category_filter = None if selected_category == 'All' else selected_category
    products = api.get_products(category=category_filter)
    
    if not products:
        st.info("No products found.")
        return
    
    # display products in grid
    cols = st.columns(3)
    
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="product-card" style="height: 100%;">
                    <h4>{product['name']}</h4>
                    <p style="color: #8b8b8b;">{product['category']}</p>
                    <h3 style="color: #667eea;">${product['price']}</h3>
                    <p>⭐ {product['rating']}/5.0</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"View Details", key=f"prod_{product['id']}"):
                st.info(f"**{product['name']}**\n\n{product['description']}")


if __name__ == "__main__":
    main()