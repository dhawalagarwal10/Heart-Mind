import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import random

from app.models.product import Product
from app.models.user import User
from app.models.interaction import Interaction
from app.config import get_settings

settings = get_settings()


class RecommenderEngine:
    """Hybrid recommendation system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.interaction_weights = {
            'view': 1.0,
            'cart': 2.0,
            'wishlist': 3.0,
            'purchase': 5.0,
            'rating': 4.0
        }
    
    def get_recommendations(
        self, 
        user_id: int, 
        n: int = 10,
        include_serendipity: bool = True
    ) -> List[Dict]:
        """
        Get personalized recommendations for a user
        Returns list of dicts with product and score
        """
        # get user's interaction history
        interactions = self._get_user_interactions(user_id)
        
        if len(interactions) < settings.MIN_INTERACTIONS_FOR_COLLABORATIVE:
            # cold start: use popularity + content-based
            return self._cold_start_recommendations(user_id, n)
        
        # warm start: hybrid approach
        collab_recs = self._collaborative_filtering(user_id, interactions)
        content_recs = self._content_based_filtering(user_id, interactions)
        
        # merge and rank
        merged = self._merge_recommendations(collab_recs, content_recs)
        
        # add serendipity
        if include_serendipity:
            merged = self._add_serendipity(merged, user_id)
        
        # get top N
        top_recs = sorted(merged, key=lambda x: x['score'], reverse=True)[:n]
        
        # enrich with product details
        return self._enrich_recommendations(top_recs)
    
    def _get_user_interactions(self, user_id: int) -> List[Interaction]:
        """Get all interactions for a user"""
        return self.db.query(Interaction).filter(
            Interaction.user_id == user_id
        ).all()
    
    def _collaborative_filtering(
        self, 
        user_id: int, 
        interactions: List[Interaction]
    ) -> List[Dict]:
        """
        User-based collaborative filtering
        Find similar users and recommend what they liked
        """
        # build user-item matrix
        user_item_matrix = self._build_user_item_matrix()
        
        if user_id not in user_item_matrix:
            return []
        
        # calculate user similarity
        target_vector = user_item_matrix[user_id]
        similarities = {}
        
        for other_user_id, other_vector in user_item_matrix.items():
            if other_user_id == user_id:
                continue
            
            # cosine similarity
            sim = self._cosine_similarity(target_vector, other_vector)
            if sim > 0:
                similarities[other_user_id] = sim
        
        # get recommendations from similar users
        recommendations = defaultdict(float)
        user_product_ids = set(target_vector.keys())
        
        for other_user_id, similarity in sorted(
            similarities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]:  # top 10 similar users
            other_vector = user_item_matrix[other_user_id]
            
            for product_id, weight in other_vector.items():
                if product_id not in user_product_ids:
                    recommendations[product_id] += weight * similarity
        
        return [
            {'product_id': pid, 'score': score, 'source': 'collaborative'}
            for pid, score in recommendations.items()
        ]
    
    def _content_based_filtering(
        self, 
        user_id: int, 
        interactions: List[Interaction]
    ) -> List[Dict]:
        """
        Content-based filtering
        Recommend similar products based on content features
        """
        # get products user has interacted with
        interacted_product_ids = [i.product_id for i in interactions]
        interacted_products = self.db.query(Product).filter(
            Product.id.in_(interacted_product_ids)
        ).all()
        
        if not interacted_products:
            return []
        
        # build product profiles
        all_products = self.db.query(Product).all()
        product_profiles = {}
        
        for product in all_products:
            # combine text features
            text = f"{product.name} {product.category} {' '.join(product.tags or [])}"
            product_profiles[product.id] = text
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        product_ids = list(product_profiles.keys())
        texts = [product_profiles[pid] for pid in product_ids]
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # calculate average profile of liked products
        liked_indices = [product_ids.index(p.id) for p in interacted_products]
        liked_vectors = tfidf_matrix[liked_indices]
        user_profile = np.asarray(liked_vectors.mean(axis=0))
        
        # find similar products
        similarities = cosine_similarity(user_profile, tfidf_matrix)[0]
        
        recommendations = []
        for idx, similarity in enumerate(similarities):
            product_id = product_ids[idx]
            if product_id not in interacted_product_ids and similarity > 0:
                recommendations.append({
                    'product_id': product_id,
                    'score': float(similarity),
                    'source': 'content'
                })
        
        return recommendations
    
    def _cold_start_recommendations(self, user_id: int, n: int) -> List[Dict]:
        """Recommendations for new users (popularity-based)"""
        # get popular products (most interactions)
        popular = self.db.query(
            Interaction.product_id,
            func.count(Interaction.id).label('interaction_count'),
            func.avg(Interaction.weight).label('avg_weight')
        ).group_by(
            Interaction.product_id
        ).order_by(
            func.count(Interaction.id).desc()
        ).limit(n * 2).all()
        
        recommendations = [
            {
                'product_id': p.product_id,
                'score': float(p.interaction_count * p.avg_weight),
                'source': 'popularity'
            }
            for p in popular
        ]
        
        return self._enrich_recommendations(recommendations[:n])
    
    def _merge_recommendations(
        self, 
        collab: List[Dict], 
        content: List[Dict]
    ) -> List[Dict]:
        """Merge collaborative and content-based recommendations"""
        merged = defaultdict(lambda: {'score': 0, 'sources': []})
        
        # weight: 60% collaborative, 40% content
        for rec in collab:
            pid = rec['product_id']
            merged[pid]['score'] += rec['score'] * 0.6
            merged[pid]['sources'].append('collaborative')
        
        for rec in content:
            pid = rec['product_id']
            merged[pid]['score'] += rec['score'] * 0.4
            merged[pid]['sources'].append('content')
        
        return [
            {
                'product_id': pid,
                'score': data['score'],
                'source': '+'.join(set(data['sources']))
            }
            for pid, data in merged.items()
        ]
    
    def _add_serendipity(
        self, 
        recommendations: List[Dict], 
        user_id: int
    ) -> List[Dict]:
        """Add unexpected but interesting recommendations"""
        n_serendipity = max(1, int(len(recommendations) * settings.SERENDIPITY_FACTOR))
        
        # get user's categories
        user_interactions = self._get_user_interactions(user_id)
        user_product_ids = [i.product_id for i in user_interactions]
        user_products = self.db.query(Product).filter(
            Product.id.in_(user_product_ids)
        ).all()
        user_categories = set(p.category for p in user_products)
        
        # find products from different categories
        recommended_ids = [r['product_id'] for r in recommendations]
        different_products = self.db.query(Product).filter(
            ~Product.category.in_(user_categories),
            ~Product.id.in_(recommended_ids + user_product_ids),
            Product.rating >= 4.0  # high quality only
        ).limit(n_serendipity * 3).all()
        
        if different_products:
            serendipity_picks = random.sample(
                different_products, 
                min(n_serendipity, len(different_products))
            )
            
            for product in serendipity_picks:
                recommendations.append({
                    'product_id': product.id,
                    'score': 0.5,  # medium score
                    'source': 'serendipity'
                })
        
        return recommendations
    
    def _enrich_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Add product details to recommendations"""
        product_ids = [r['product_id'] for r in recommendations]
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids)
        ).all()
        
        product_map = {p.id: p for p in products}
        
        enriched = []
        for rec in recommendations:
            product = product_map.get(rec['product_id'])
            if product:
                enriched.append({
                    **rec,
                    'product': product.to_dict()
                })
        
        return enriched
    
    def _build_user_item_matrix(self) -> Dict[int, Dict[int, float]]:
        """Build sparse user-item interaction matrix"""
        interactions = self.db.query(Interaction).all()
        
        matrix = defaultdict(lambda: defaultdict(float))
        
        for interaction in interactions:
            weight = self.interaction_weights.get(
                interaction.interaction_type, 
                1.0
            )
            matrix[interaction.user_id][interaction.product_id] += weight
        
        return dict(matrix)
    
    @staticmethod
    def _cosine_similarity(vec1: Dict, vec2: Dict) -> float:
        """Calculate cosine similarity between two sparse vectors"""
        common_keys = set(vec1.keys()) & set(vec2.keys())
        
        if not common_keys:
            return 0.0
        
        dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
        mag1 = np.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = np.sqrt(sum(v**2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)