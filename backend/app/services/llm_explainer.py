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
        'friendly': {
            'persona': 'You are an enthusiastic shopping friend who genuinely wants them to have the best.',
            'style': 'Be warm, excited, and use words like "perfect", "exactly", "love". Create urgency through enthusiasm. Make them feel this is THE ONE. Use exclamation points sparingly but effectively.'
        },
        'expert': {
            'persona': 'You are a data-driven shopping consultant with insider knowledge.',
            'style': 'Use statistics, ratings, and comparisons. Create urgency through logic and data. Phrase it as an "obvious choice" based on their patterns. Be authoritative but helpful.'
        },
        'storyteller': {
            'persona': 'You are a master storyteller who makes products come alive.',
            'style': 'Paint a vivid picture of life WITH this product. Use sensory details. Create emotional connection. Make them imagine the future with it. Build narrative tension and release.'
        },
        'minimalist': {
            'persona': 'You are a direct, no-BS advisor who cuts to the chase.',
            'style': 'ONE powerful sentence. Maximum 12 words. Use strong verbs. Make every word count. Create urgency through brevity. No fluff, pure impact.'
        }
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
        """Generate explanation for why a product is recommended"""
        
        # get rich user context
        user = self.db.query(User).filter(User.id == user_id).first()
        user_context = self._get_rich_user_context(user_id)
        
        # build enhanced prompt
        prompt = self._build_enhanced_prompt(
            user=user,
            user_context=user_context,
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
            print(f"LLM Error: {e}")
            return self._fallback_explanation(product, recommendation_source, user_context)
    
    def _build_enhanced_prompt(
        self,
        user: Optional[User],
        user_context: Dict,
        product: Dict,
        source: str,
        personality: str
    ) -> str:
        """Build a rich, contextual prompt for better explanations"""
        
        personality_config = self.PERSONALITIES.get(personality, self.PERSONALITIES['friendly'])
        
        # build recent purchases string
        recent_purchases = ""
        if user_context['recent_purchases']:
            recent_purchases = "Recent purchases: " + ", ".join([
                f"{p['name']} (${p['price']})" 
                for p in user_context['recent_purchases'][:3]
            ])
        
        # build browsing patterns
        browsing_pattern = ""
        if user_context['top_categories']:
            top_cat = user_context['top_categories'][0]
            browsing_pattern = f"Spends {top_cat['percentage']:.0f}% of time browsing {top_cat['category']}"
        
        # build price preference
        price_insight = ""
        if user_context['avg_purchase_price'] > 0:
            price_insight = f"Typically purchases items around ${user_context['avg_purchase_price']:.0f}"
        
        # calculate value proposition
        value_angle = self._identify_value_angle(product, user_context)
        psychological_trigger = self._get_psychological_trigger(source, user_context, product)
        
        prompt = f"""{personality_config['persona']}

{personality_config['style']}

USER PROFILE:
- Name: {user.name if user else 'This shopper'}
- Shopping Behavior: {user_context['interaction_count']} interactions, {user_context['purchase_count']} purchases
- {browsing_pattern}
- {price_insight}
- {recent_purchases}
- Engagement Level: {user_context['engagement_level']}

PRODUCT BEING RECOMMENDED:
- Name: {product['name']}
- Category: {product['category']}
- Price: ${product['price']:.2f}
- Rating: {product['rating']}/5.0 ({"High" if product['rating'] >= 4.5 else "Good"} rated)
- Tags: {', '.join(product.get('tags', []))}

WHY IT'S RECOMMENDED:
{self._format_recommendation_reason(source, user_context, product)}

VALUE PROPOSITION FOR THIS USER:
{value_angle}

PSYCHOLOGICAL TRIGGER TO USE:
{psychological_trigger}

YOUR MISSION - MAKE THEM WANT TO BUY:
Write a compelling, persuasive 2-3 sentence explanation that makes this user genuinely excited to purchase this product.

PERSUASION TECHNIQUES TO USE:
1. **Scarcity/Urgency**: Imply this matches a rare opportunity or gap in their collection
2. **Social Proof**: Reference the high rating as validation from others like them
3. **Loss Aversion**: Subtly hint at what they'd miss by not getting this
4. **Pattern Completion**: Show how this completes or enhances their existing purchases
5. **Emotional Appeal**: Connect to lifestyle, aspirations, or past positive experiences
6. **Logical Justification**: Give them a rational reason to justify an emotional decision
7. **Value Emphasis**: Highlight the amazing value relative to their spending patterns
8. **Exclusivity**: Make them feel this pick is specially curated for them
9. **Problem-Solution**: Address a need they have (even if they don't know it yet)
10. **Future Pacing**: Help them imagine life WITH this product

EXAMPLES OF PERSUASIVE LANGUAGE:
- "This is EXACTLY the missing piece in your [category] collection"
- "Given your love for [past purchase], this is a no-brainer"
- "At $X, this is a steal compared to your usual $Y range"
- "Thousands of shoppers rated this 4.8/5 - they can't all be wrong"
- "The perfect companion to your recent [product] purchase"
- "This bridges the gap between your [category1] and [category2] interests"
- "You've been circling around [category] - this is your sign to dive in"
- "Imagine having this for [upcoming scenario/season/event]"

CRITICAL RULES:
- NEVER say "based on your preferences" or generic phrases
- ALWAYS reference specific past behavior or purchases by name
- Make it feel like a personal recommendation from a friend who knows them
- Create FOMO (fear of missing out) without being pushy
- Use power words: perfect, exactly, ideal, amazing, steal, essential, game-changer
- End with forward momentum - make them imagine owning it
- For minimalist: ONE punchy, irresistible sentence

Generate the persuasive explanation NOW:"""
        
        return prompt
    
    def _get_rich_user_context(self, user_id: int) -> Dict:
        """Get comprehensive user behavioral context"""
        
        # get all interactions
        interactions = self.db.query(Interaction).filter(
            Interaction.user_id == user_id
        ).order_by(Interaction.timestamp.desc()).all()
        
        if not interactions:
            return {
                'interaction_count': 0,
                'purchase_count': 0,
                'recent_purchases': [],
                'top_categories': [],
                'avg_purchase_price': 0,
                'engagement_level': 'New User',
                'favorite_tags': []
            }
        
        # get product details
        product_ids = list(set([i.product_id for i in interactions]))
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()
        product_map = {p.id: p for p in products}
        
        # analyze purchases
        purchases = [i for i in interactions if i.interaction_type == 'purchase']
        recent_purchases = []
        purchase_prices = []
        
        for purchase in purchases[:5]:  # last 5 purchases
            product = product_map.get(purchase.product_id)
            if product:
                recent_purchases.append({
                    'name': product.name,
                    'price': product.price,
                    'category': product.category
                })
                purchase_prices.append(product.price)
        
        # category breakdown
        category_counts = {}
        all_tags = []
        
        for interaction in interactions:
            product = product_map.get(interaction.product_id)
            if product:
                category_counts[product.category] = category_counts.get(product.category, 0) + 1
                all_tags.extend(product.tags or [])
        
        # top categories with percentages
        total_interactions = len(interactions)
        top_categories = [
            {
                'category': cat,
                'count': count,
                'percentage': (count / total_interactions) * 100
            }
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # engagement level
        if len(interactions) < 5:
            engagement = "New Explorer"
        elif len(interactions) < 15:
            engagement = "Regular Browser"
        elif len(purchases) > 5:
            engagement = "Loyal Customer"
        else:
            engagement = "Active Shopper"
        
        # favorite tags
        from collections import Counter
        tag_counts = Counter(all_tags)
        favorite_tags = [tag for tag, _ in tag_counts.most_common(5)]
        
        return {
            'interaction_count': len(interactions),
            'purchase_count': len(purchases),
            'recent_purchases': recent_purchases,
            'top_categories': top_categories,
            'avg_purchase_price': sum(purchase_prices) / len(purchase_prices) if purchase_prices else 0,
            'engagement_level': engagement,
            'favorite_tags': favorite_tags
        }
    
    def _identify_value_angle(self, product: Dict, user_context: Dict) -> str:
        """Identify the strongest value proposition for this user"""
        
        angles = []
        
        # price angle
        if user_context['avg_purchase_price'] > 0:
            if product['price'] < user_context['avg_purchase_price'] * 0.7:
                angles.append(f"BARGAIN: At ${product['price']:.2f}, this is significantly below your usual ${user_context['avg_purchase_price']:.0f} spending - incredible value")
            elif abs(product['price'] - user_context['avg_purchase_price']) < user_context['avg_purchase_price'] * 0.2:
                angles.append(f"SWEET SPOT: ${product['price']:.2f} hits your comfort zone perfectly")
            else:
                angles.append(f"INVESTMENT: ${product['price']:.2f} - premium quality worth the upgrade")
        
        # rating angle
        if product['rating'] >= 4.7:
            angles.append(f"VALIDATED: {product['rating']}/5 rating = proven excellence, trusted by thousands")
        elif product['rating'] >= 4.3:
            angles.append(f"RELIABLE: Solid {product['rating']}/5 rating = consistent quality")
        
        # category angle
        if user_context['top_categories']:
            top_cat = user_context['top_categories'][0]
            if product['category'] == top_cat['category']:
                angles.append(f"EXPERTISE MATCH: You know {top_cat['category']} well - this enhances your collection")
            else:
                angles.append(f"EXPANSION: Diversifies beyond your {top_cat['category']} focus into new territory")
        
        # purchase history angle
        if user_context['purchase_count'] > 5:
            angles.append(f"LOYAL CUSTOMER PICK: As someone with {user_context['purchase_count']} purchases, you'll appreciate this quality")
        
        return " | ".join(angles[:3]) if angles else "High-value recommendation"
    
    def _get_psychological_trigger(self, source: str, user_context: Dict, product: Dict) -> str:
        """Identify the best psychological persuasion trigger"""
        
        triggers = []
        
        # scarcity / FOMO
        if source == 'serendipity':
            triggers.append("DISCOVERY: This rare find won't appear again - serendipity recommendations are unique")
        
        # social proof
        if product['rating'] >= 4.5:
            triggers.append(f"SOCIAL PROOF: Join thousands who rated this {product['rating']}/5")
        
        # pattern completion
        if user_context['recent_purchases']:
            last_purchase = user_context['recent_purchases'][0]
            triggers.append(f"COMPLETION: The perfect companion to your {last_purchase['name']}")
        
        # consistency principle
        if user_context['purchase_count'] > 3:
            triggers.append(f"CONSISTENCY: You've built great taste with {user_context['purchase_count']} purchases - continue the streak")
        
        # loss aversion
        if product['price'] < user_context['avg_purchase_price']:
            triggers.append(f"LOSS AVERSION: Don't miss this below-average-price opportunity")
        
        # authority
        if product['rating'] >= 4.6:
            triggers.append("AUTHORITY: Expert-level ratings validate this choice")
        
        # reciprocity
        if user_context['engagement_level'] in ['Loyal Customer', 'Active Shopper']:
            triggers.append("RECIPROCITY: As a valued shopper, you deserve this premium recommendation")
        
        return triggers[0] if triggers else "HIGH RECOMMENDATION CONFIDENCE"
    
    def _format_recommendation_reason(self, source: str, user_context: Dict, product: Dict) -> str:
        """Format the reasoning based on recommendation source"""
        
        reasons = []
        
        if source == 'collaborative':
            reasons.append("Users with similar shopping patterns love this product")
            
        if source == 'content':
            if user_context['top_categories']:
                top_cat = user_context['top_categories'][0]['category']
                if product['category'] == top_cat:
                    reasons.append(f"Aligns perfectly with your interest in {top_cat}")
                    
        if source == 'serendipity':
            reasons.append("This is outside your usual categories but highly rated - a discovery pick")
            reasons.append(f"Expanding beyond your typical {user_context['top_categories'][0]['category'] if user_context['top_categories'] else 'categories'}")
            
        if 'collaborative' in source and 'content' in source:
            reasons.append("Combines popularity among similar shoppers AND matches your browsing patterns")
        
        # price match
        if user_context['avg_purchase_price'] > 0:
            price_diff = abs(product['price'] - user_context['avg_purchase_price'])
            if price_diff < user_context['avg_purchase_price'] * 0.3:  # Within 30%
                reasons.append(f"Price point (${product['price']:.2f}) matches your usual range")
        
        # high rating
        if product['rating'] >= 4.5:
            reasons.append(f"Exceptional {product['rating']}/5.0 rating indicates quality")
        
        return " | ".join(reasons) if reasons else "Recommended based on your shopping behavior"
    
    def _fallback_explanation(self, product: Dict, source: str, user_context: Dict) -> str:
        """Enhanced PERSUASIVE fallback explanation"""
        
        if source == 'serendipity':
            return f"🌟 This {product['rating']}/5 star gem from {product['category']} is your chance to discover something amazing outside your usual picks. High ratings don't lie - thousands already love it at just ${product['price']:.2f}!"
        
        if user_context['top_categories']:
            top_cat = user_context['top_categories'][0]['category']
            if product['category'] == top_cat:
                if user_context['purchase_count'] > 0:
                    return f"Given your {user_context['purchase_count']} purchases in {top_cat}, you clearly know quality when you see it. This {product['rating']}/5 rated {product['name']} is exactly what belongs in your collection at ${product['price']:.2f}!"
                return f"You spend {top_cat['percentage']:.0f}% of your time browsing {top_cat} - this {product['rating']}/5 rated gem is EXACTLY what you're looking for!"
        
        # general persuasive fallback
        if product['rating'] >= 4.5:
            return f"With a stellar {product['rating']}/5 rating, this isn't just good - it's exceptional. At ${product['price']:.2f}, you're getting proven quality that thousands trust. Don't miss this one!"
        
        return f"This {product['rating']}/5 rated {product['name']} matches your shopping DNA perfectly. ${product['price']:.2f} for quality you can count on!"
    
    async def batch_explain(
        self,
        user_id: int,
        recommendations: List[Dict],
        personality: str = 'friendly'
    ) -> List[Dict]:
        """Generate explanations for multiple recommendations"""
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
