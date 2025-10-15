import google.generativeai as genai
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from app.models.interaction import Interaction
from app.config import get_settings

settings = get_settings()


class LLMExplainer:
    """Generate natural language explanations for recommendations"""
    
    PERSONALITIES = {
        'friendly': 'You are a friendly shopping assistant. Be warm, casual, and enthusiastic.',
        'expert': 'You are a product expert. Be knowledgeable, precise, and professional.',
        'storyteller': 'You are a storyteller. Create engaging narratives around products.',
        'minimalist': 'You are concise and direct. Get to the point quickly.'
    }
    
    def __init__(self, db: Session):
        self.db = db
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
    
    async def explain_recommendation(
        self,
        user_id: int,
        product: Dict,
        recommendation_source: str,
        personality: str = 'friendly'
    ) -> str:
        """
        Generate explanation for why a product is recommended
        
        Args:
            user_id: The user receiving the recommendation
            product: Product dictionary
            recommendation_source: How it was recommended ('collaborative', 'content', 'serendipity')
            personality: Explanation style
        
        Returns:
            Natural language explanation
        """
        # get user context
        user = self.db.query(User).filter(User.id == user_id).first()
        user_history = self._get_user_context(user_id)
        
        # build prompt
        prompt = self._build_explanation_prompt(
            user=user,
            user_history=user_history,
            product=product,
            source=recommendation_source,
            personality=personality
        )
        
        # call gemini API
        try:
            generation_config = {
                "temperature": settings.EXPLANATION_TEMPERATURE,
                "max_output_tokens": settings.LLM_MAX_TOKENS,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            explanation = response.text.strip()
            return explanation
            
        except Exception as e:
            # fallback explanation
            return self._fallback_explanation(product, recommendation_source)
    
    def _build_explanation_prompt(
        self,
        user: Optional[User],
        user_history: Dict,
        product: Dict,
        source: str,
        personality: str
    ) -> str:
        """Build the prompt for Claude"""
        
        system_persona = self.PERSONALITIES.get(personality, self.PERSONALITIES['friendly'])
        
        prompt = f"""{system_persona}

A user is browsing an e-commerce store. Based on their behavior, we're recommending a product to them.

USER CONTEXT:
- Name: {user.name if user else 'Guest'}
- Previously viewed categories: {', '.join(user_history['categories']) if user_history['categories'] else 'None yet'}
- Recent interactions: {user_history['recent_summary']}
- Preferred price range: {user_history['price_range']}

RECOMMENDED PRODUCT:
- Name: {product['name']}
- Category: {product['category']}
- Price: ${product['price']:.2f}
- Rating: {product['rating']}/5.0
- Description: {product['description']}

RECOMMENDATION REASON:
{self._format_recommendation_reason(source, user_history)}

TASK:
Write a compelling 2-3 sentence explanation for why this product is recommended to this user. 
Make it personal, engaging, and actionable. Focus on value and fit.
DO NOT use phrases like "I recommend" or "You should buy" - instead explain why it's a good match.
"""
        
        return prompt
    
    def _format_recommendation_reason(self, source: str, user_history: Dict) -> str:
        """Format the reasoning based on recommendation source"""
        if source == 'collaborative':
            return "This product is popular with users who have similar tastes to this user."
        elif source == 'content':
            return f"This product is similar to items they've shown interest in: {', '.join(user_history['categories'][:3])}"
        elif source == 'serendipity':
            return "This is outside their usual preferences but highly rated - a discovery recommendation."
        elif 'collaborative' in source and 'content' in source:
            return "This combines similarity to their interests AND popularity with like-minded shoppers."
        else:
            return "This is a trending product that matches their browsing patterns."
    
    def _get_user_context(self, user_id: int) -> Dict:
        """Get user's behavioral context"""
        interactions = self.db.query(Interaction).filter(
            Interaction.user_id == user_id
        ).order_by(Interaction.timestamp.desc()).limit(20).all()
        
        if not interactions:
            return {
                'categories': [],
                'recent_summary': 'This is a new user just starting to explore.',
                'price_range': 'Not yet determined'
            }
        
        # get product details
        product_ids = [i.product_id for i in interactions]
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()
        
        product_map = {p.id: p for p in products}
        
        # analyze patterns
        categories = []
        prices = []
        purchases = 0
        
        for interaction in interactions:
            product = product_map.get(interaction.product_id)
            if product:
                categories.append(product.category)
                prices.append(product.price)
                if interaction.interaction_type == 'purchase':
                    purchases += 1
        
        # build summary
        unique_categories = list(set(categories))
        recent_summary = f"Viewed {len(interactions)} products"
        if purchases > 0:
            recent_summary += f", purchased {purchases} items"
        
        price_range = 'Any price'
        if prices:
            avg_price = sum(prices) / len(prices)
            if avg_price < 30:
                price_range = 'Budget-friendly ($0-$30)'
            elif avg_price < 100:
                price_range = 'Mid-range ($30-$100)'
            else:
                price_range = 'Premium ($100+)'
        
        return {
            'categories': unique_categories,
            'recent_summary': recent_summary,
            'price_range': price_range
        }
    
    def _fallback_explanation(self, product: Dict, source: str) -> str:
        """Fallback explanation if LLM fails"""
        if source == 'serendipity':
            return f"We thought you might enjoy exploring {product['name']} - it's highly rated and offers something different from your usual picks!"
        elif source == 'collaborative':
            return f"Based on your taste, {product['name']} is popular with shoppers who have similar preferences."
        else:
            return f"{product['name']} matches your interests in {product['category']} and has a {product['rating']}/5 rating."
    
    async def batch_explain(
        self,
        user_id: int,
        recommendations: List[Dict],
        personality: str = 'friendly'
    ) -> List[Dict]:
        """
        Generate explanations for multiple recommendations
        Returns recommendations enriched with explanations
        """
        enriched = []
        
        for rec in recommendations:
            explanation = await self.explain_recommendation(
                user_id=user_id,
                product=rec['product'],
                recommendation_source=rec['source'],
                personality=personality
            )
            
            enriched.append({
                **rec,
                'explanation': explanation
            })
        
        return enriched
    
    def explain_counterfactual(
        self,
        user_id: int,
        product_id: int,
        reason: str = "price"
    ) -> str:
        """
        Generate counterfactual explanation
        "What would make this product better for you?"
        """
        prompt = f"""A user is viewing a product but hasn't added it to cart.
Explain in ONE sentence what might make them more likely to purchase it.

Reason for hesitation: {reason}

Be specific and actionable. Start with "Consider this product when..." or "This would be perfect if..."
"""
        
        try:
            generation_config = {
                "temperature": 0.7,
                "max_output_tokens": 100,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text.strip()
        except:
            return f"This product might be a better fit if you're looking for {reason}-related features."