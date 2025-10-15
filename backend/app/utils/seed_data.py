import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.product import Product
from app.models.user import User
from app.models.interaction import Interaction


# sample product data
PRODUCTS = [
    # electronics
    {"name": "Wireless Noise-Canceling Headphones", "category": "Electronics", "price": 299.99, "rating": 4.7,
     "description": "Premium wireless headphones with active noise cancellation and 30-hour battery life",
     "tags": ["audio", "wireless", "premium"], "stock": 50},
    {"name": "4K Smart TV 55-inch", "category": "Electronics", "price": 599.99, "rating": 4.5,
     "description": "Ultra HD smart TV with HDR and built-in streaming apps",
     "tags": ["tv", "4k", "smart"], "stock": 30},
    {"name": "Laptop Stand Aluminum", "category": "Electronics", "price": 49.99, "rating": 4.8,
     "description": "Ergonomic laptop stand with adjustable height and cable management",
     "tags": ["accessories", "ergonomic"], "stock": 100},
    {"name": "Wireless Gaming Mouse", "category": "Electronics", "price": 79.99, "rating": 4.6,
     "description": "High-precision gaming mouse with customizable RGB lighting",
     "tags": ["gaming", "wireless", "rgb"], "stock": 75},
    {"name": "USB-C Hub 7-in-1", "category": "Electronics", "price": 39.99, "rating": 4.4,
     "description": "Multi-port USB-C hub with HDMI, USB 3.0, and SD card reader",
     "tags": ["accessories", "usb-c"], "stock": 120},
    
    # fashion
    {"name": "Leather Crossbody Bag", "category": "Fashion", "price": 129.99, "rating": 4.6,
     "description": "Genuine leather crossbody bag with adjustable strap",
     "tags": ["bags", "leather", "premium"], "stock": 40},
    {"name": "Classic Denim Jacket", "category": "Fashion", "price": 89.99, "rating": 4.5,
     "description": "Timeless denim jacket with button closure",
     "tags": ["outerwear", "denim", "casual"], "stock": 60},
    {"name": "Running Shoes Pro", "category": "Fashion", "price": 149.99, "rating": 4.8,
     "description": "Professional running shoes with cushioned sole and breathable mesh",
     "tags": ["shoes", "sports", "premium"], "stock": 80},
    {"name": "Wool Beanie Hat", "category": "Fashion", "price": 24.99, "rating": 4.3,
     "description": "Warm wool beanie perfect for winter",
     "tags": ["accessories", "winter"], "stock": 150},
    {"name": "Sunglasses UV Protection", "category": "Fashion", "price": 59.99, "rating": 4.4,
     "description": "Stylish sunglasses with 100% UV protection",
     "tags": ["accessories", "summer"], "stock": 90},
    
    # home & kitchen
    {"name": "Espresso Machine Deluxe", "category": "Home & Kitchen", "price": 399.99, "rating": 4.7,
     "description": "Professional-grade espresso machine with milk frother",
     "tags": ["coffee", "appliances", "premium"], "stock": 25},
    {"name": "Air Fryer 5.8 Quart", "category": "Home & Kitchen", "price": 129.99, "rating": 4.6,
     "description": "Large capacity air fryer with digital controls",
     "tags": ["cooking", "appliances", "healthy"], "stock": 45},
    {"name": "Bamboo Cutting Board Set", "category": "Home & Kitchen", "price": 34.99, "rating": 4.5,
     "description": "3-piece bamboo cutting board set with juice grooves",
     "tags": ["kitchenware", "eco-friendly"], "stock": 100},
    {"name": "Robot Vacuum Cleaner", "category": "Home & Kitchen", "price": 279.99, "rating": 4.4,
     "description": "Smart robot vacuum with app control and auto-charging",
     "tags": ["cleaning", "smart", "automation"], "stock": 35},
    {"name": "Weighted Blanket 15 lbs", "category": "Home & Kitchen", "price": 79.99, "rating": 4.7,
     "description": "Therapeutic weighted blanket for better sleep",
     "tags": ["bedding", "wellness"], "stock": 50},
    
    # sports & outdoors
    {"name": "Yoga Mat Premium", "category": "Sports & Outdoors", "price": 49.99, "rating": 4.8,
     "description": "Extra-thick yoga mat with non-slip surface and carrying strap",
     "tags": ["yoga", "fitness", "accessories"], "stock": 80},
    {"name": "Camping Tent 4-Person", "category": "Sports & Outdoors", "price": 199.99, "rating": 4.5,
     "description": "Waterproof camping tent with easy setup",
     "tags": ["camping", "outdoor", "family"], "stock": 30},
    {"name": "Resistance Bands Set", "category": "Sports & Outdoors", "price": 29.99, "rating": 4.6,
     "description": "5-piece resistance band set for home workouts",
     "tags": ["fitness", "home-gym"], "stock": 120},
    {"name": "Water Bottle Insulated", "category": "Sports & Outdoors", "price": 34.99, "rating": 4.7,
     "description": "32oz insulated water bottle keeps drinks cold for 24 hours",
     "tags": ["hydration", "eco-friendly"], "stock": 150},
    {"name": "Hiking Backpack 40L", "category": "Sports & Outdoors", "price": 89.99, "rating": 4.6,
     "description": "Durable hiking backpack with multiple compartments",
     "tags": ["hiking", "backpack", "outdoor"], "stock": 45},
    
    # books & media
    {"name": "Kindle E-Reader", "category": "Books & Media", "price": 139.99, "rating": 4.7,
     "description": "Digital e-reader with adjustable backlight and weeks of battery",
     "tags": ["ereader", "books", "digital"], "stock": 60},
    {"name": "Bluetooth Speaker Portable", "category": "Books & Media", "price": 79.99, "rating": 4.5,
     "description": "Waterproof portable speaker with 12-hour battery",
     "tags": ["audio", "bluetooth", "portable"], "stock": 90},
    {"name": "Board Game Strategy", "category": "Books & Media", "price": 44.99, "rating": 4.6,
     "description": "Award-winning strategy board game for 2-4 players",
     "tags": ["games", "family", "strategy"], "stock": 70},
    {"name": "Vinyl Record Player", "category": "Books & Media", "price": 249.99, "rating": 4.4,
     "description": "Vintage-style record player with built-in speakers",
     "tags": ["audio", "vinyl", "retro"], "stock": 25},
    {"name": "Puzzle 1000 Pieces", "category": "Books & Media", "price": 19.99, "rating": 4.3,
     "description": "Challenging 1000-piece jigsaw puzzle",
     "tags": ["puzzle", "family"], "stock": 100},
]

# sample users
USERS = [
    {"email": "arjun@example.com", "name": "Arjun Singh", "preferences": {"budget": "mid-range"}},
    {"email": "jiya@example.com", "name": "Jiya Patel", "preferences": {"interests": ["home", "cooking"]}},
    {"email": "divys@example.com", "name": "Divya Sharma", "preferences": {"interests": ["fitness", "wellness"]}},
    {"email": "kartik@example.com", "name": "Kartik Mehta", "preferences": {"budget": "premium"}},
    {"email": "rohan@example.com", "name": "Rohan Gupta", "preferences": {"interests": ["tech", "gaming"]}},
]


def seed_products(db: Session):
    """Seed products into database"""
    print("🌱 Seeding products...")
    
    for product_data in PRODUCTS:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print(f"✅ Added {len(PRODUCTS)} products")


def seed_users(db: Session):
    """Seed users into database"""
    print("🌱 Seeding users...")
    
    for user_data in USERS:
        user = User(**user_data)
        db.add(user)
    
    db.commit()
    print(f"✅ Added {len(USERS)} users")


def seed_interactions(db: Session):
    """Seed realistic interactions"""
    print("🌱 Seeding interactions...")
    
    users = db.query(User).all()
    products = db.query(Product).all()
    
    interaction_types = ['view', 'cart', 'wishlist', 'purchase']
    weights = {'view': 1.0, 'cart': 2.0, 'wishlist': 3.0, 'purchase': 5.0}
    
    # generate realistic interaction patterns
    interactions_count = 0
    
    for user in users:
        # each user has 10-30 interactions
        num_interactions = random.randint(10, 30)
        
        # user's preferred categories (simulate behavioral patterns)
        if 'tech' in user.preferences.get('interests', []):
            category_preferences = ['Electronics', 'Books & Media']
        elif 'fitness' in user.preferences.get('interests', []):
            category_preferences = ['Sports & Outdoors', 'Fashion']
        elif 'home' in user.preferences.get('interests', []):
            category_preferences = ['Home & Kitchen']
        else:
            category_preferences = random.sample(
                ['Electronics', 'Fashion', 'Home & Kitchen', 'Sports & Outdoors', 'Books & Media'],
                k=2
            )
        
        # generate interactions
        for _ in range(num_interactions):
            # 70% from preferred categories, 30% exploration
            if random.random() < 0.7:
                category_products = [p for p in products if p.category in category_preferences]
                product = random.choice(category_products if category_products else products)
            else:
                product = random.choice(products)
            
            # interaction type probabilities: view 50%, cart 30%, wishlist 10%, purchase 10%
            interaction_type = random.choices(
                interaction_types,
                weights=[50, 30, 10, 10]
            )[0]
            
            # random timestamp within last 30 days
            days_ago = random.randint(0, 30)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            interaction = Interaction(
                user_id=user.id,
                product_id=product.id,
                interaction_type=interaction_type,
                weight=weights[interaction_type],
                timestamp=timestamp
            )
            
            db.add(interaction)
            interactions_count += 1
    
    db.commit()
    print(f"✅ Added {interactions_count} interactions")


def seed_all():
    """Seed all data"""
    print("\n🚀 Starting database seeding...\n")
    
    # initialize database
    init_db()
    
    # create session
    db = SessionLocal()
    
    try:
        # check if already seeded
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print("⚠️  Database already seeded. Skipping...")
            return
        
        # seed data
        seed_products(db)
        seed_users(db)
        seed_interactions(db)
        
        print("\n✨ Database seeding completed successfully!\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()