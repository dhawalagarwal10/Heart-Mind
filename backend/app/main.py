from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import get_db, init_db
from app.models.product import Product, ProductSchema, ProductCreate
from app.models.user import User, UserSchema, UserCreate
from app.models.interaction import Interaction, InteractionCreate, InteractionSchema
from app.services.recommender import RecommenderEngine
from app.services.llm_explainer import LLMExplainer

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    print("✨ Heart&Mind Recommender System Started!")
    print(f"📊 Database: {settings.DATABASE_URL}")
    yield
    print("👋 Shutting down...")


# create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HEALTH CHECK

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# PRODUCT ENDPOINTS

@app.get("/products", response_model=List[ProductSchema])
async def get_products(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all products with optional category filter"""
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    return products


@app.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get single product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@app.post("/products", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories"""
    categories = db.query(Product.category).distinct().all()
    return [c[0] for c in categories]


# USER ENDPOINTS

@app.get("/users", response_model=List[UserSchema])
async def get_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.get("/users/{user_id}", response_model=UserSchema)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get single user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.post("/users", response_model=UserSchema)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # check if email exists
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# INTERACTION ENDPOINTS

@app.post("/interactions", response_model=InteractionSchema)
async def track_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db)
):
    """Track a user-product interaction"""
    # validate user and product exist
    user = db.query(User).filter(User.id == interaction.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    product = db.query(Product).filter(Product.id == interaction.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # set weight based on interaction type
    weights = {'view': 1.0, 'cart': 2.0, 'wishlist': 3.0, 'purchase': 5.0, 'rating': 4.0}
    weight = weights.get(interaction.interaction_type, 1.0)
    
    db_interaction = Interaction(
        **interaction.model_dump(),
        weight=weight
    )
    
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    return db_interaction


@app.get("/users/{user_id}/interactions", response_model=List[InteractionSchema])
async def get_user_interactions(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all interactions for a user"""
    interactions = db.query(Interaction).filter(
        Interaction.user_id == user_id
    ).order_by(
        Interaction.timestamp.desc()
    ).offset(skip).limit(limit).all()
    
    return interactions


# RECOMMENDATION ENDPOINTS (The Core Magic!)

@app.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id: int,
    n: int = 10,
    personality: str = 'friendly',
    include_explanations: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations with LLM explanations
    
    Args:
        user_id: User ID
        n: Number of recommendations
        personality: Explanation style ('friendly', 'expert', 'storyteller', 'minimalist')
        include_explanations: Whether to generate LLM explanations
    """
    # validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # get recommendations
    engine = RecommenderEngine(db)
    recommendations = engine.get_recommendations(user_id, n)
    
    if not recommendations:
        return {
            "user_id": user_id,
            "recommendations": [],
            "message": "Not enough data for personalized recommendations yet. Start browsing!"
        }
    
    # add LLM explanations
    if include_explanations:
        explainer = LLMExplainer(db)
        recommendations = await explainer.batch_explain(
            user_id=user_id,
            recommendations=recommendations,
            personality=personality
        )
    
    return {
        "user_id": user_id,
        "personality": personality,
        "count": len(recommendations),
        "recommendations": recommendations
    }


@app.get("/recommendations/{user_id}/explain/{product_id}")
async def explain_specific_recommendation(
    user_id: int,
    product_id: int,
    personality: str = 'friendly',
    db: Session = Depends(get_db)
):
    """Get explanation for why a specific product is recommended"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    explainer = LLMExplainer(db)
    explanation = await explainer.explain_recommendation(
        user_id=user_id,
        product=product.to_dict(),
        recommendation_source='content',
        personality=personality
    )
    
    return {
        "user_id": user_id,
        "product_id": product_id,
        "product": product.to_dict(),
        "explanation": explanation
    }


# ANALYTICS ENDPOINTS

@app.get("/analytics/user/{user_id}")
async def get_user_analytics(user_id: int, db: Session = Depends(get_db)):
    """Get user behavior analytics"""
    interactions = db.query(Interaction).filter(
        Interaction.user_id == user_id
    ).all()
    
    if not interactions:
        return {
            "user_id": user_id,
            "total_interactions": 0,
            "message": "No interaction data yet"
        }
    
    # calculate statistics
    product_ids = [i.product_id for i in interactions]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    
    categories = {}
    total_value = 0
    purchases = 0
    
    for interaction in interactions:
        product = next((p for p in products if p.id == interaction.product_id), None)
        if product:
            categories[product.category] = categories.get(product.category, 0) + 1
            
            if interaction.interaction_type == 'purchase':
                total_value += product.price
                purchases += 1
    
    return {
        "user_id": user_id,
        "total_interactions": len(interactions),
        "categories_explored": categories,
        "total_purchases": purchases,
        "total_spent": round(total_value, 2),
        "favorite_category": max(categories, key=categories.get) if categories else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )