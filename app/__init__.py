from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
import os
import sys

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None
    
    # Register blueprints
    from app.main.routes import main
    from app.auth.routes import auth
    from app.cart.routes import cart
    from app.orders.routes import orders
    from app.admin.routes import admin
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(cart, url_prefix='/cart')
    app.register_blueprint(orders, url_prefix='/orders')
    app.register_blueprint(admin, url_prefix='/admin')
    
    # Create tables and seed data
    with app.app_context():
        print("\n=== Initializing Database ===")
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create default categories if none exist
        from app.models import Category, Product
        if Category.query.count() == 0:
            print("Creating categories...")
            categories = [
                Category(name='Men', description='Men\'s Fashion Collection'),
                Category(name='Women', description='Women\'s Fashion Collection'),
                Category(name='Kids', description='Kids\' Fashion Collection'),
                Category(name='Accessories', description='Fashion Accessories')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("✓ Categories created")
        
        # Create sample products if none exist
        if Product.query.count() == 0:
            print("Creating sample products...")
            sample_products = [
                Product(
                    name='Classic White Shirt',
                    description='Premium cotton white shirt for men',
                    price=2999,
                    discount_price=1999,
                    stock=50,
                    category_id=1,
                    is_featured=True,
                    is_active=True,
                    image_url='uploads/shirt1.jpg'
                ),
                Product(
                    name='Slim Fit Jeans',
                    description='Comfortable slim fit denim jeans',
                    price=3999,
                    discount_price=2999,
                    stock=40,
                    category_id=1,
                    is_featured=True,
                    is_active=True,
                    image_url='uploads/jeans1.jpg'
                ),
                Product(
                    name='Floral Summer Dress',
                    description='Beautiful floral print summer dress',
                    price=4999,
                    discount_price=3499,
                    stock=30,
                    category_id=2,
                    is_featured=True,
                    is_active=True,
                    image_url='uploads/dress1.jpg'
                ),
                Product(
                    name='Leather Jacket',
                    description='Genuine leather jacket for men',
                    price=8999,
                    discount_price=6999,
                    stock=20,
                    category_id=1,
                    is_featured=True,
                    is_active=True,
                    image_url='uploads/jacket1.jpg'
                )
            ]
            db.session.add_all(sample_products)
            db.session.commit()
            print("✓ Sample products created")
        
        # Create admin user if not exists
        print("\n=== Checking Admin User ===")
        admin_user = User.query.filter_by(email='admin@durahe.com').first()
        
        if not admin_user:
            print("Creating new admin user...")
            admin_user = User(
                email='admin@durahe.com',
                username='admin',
                full_name='Administrator',
                phone='9999999999',
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created")
        else:
            print(f"Admin user exists: {admin_user.email}")
            print(f"Username: {admin_user.username}")
            print(f"Is Admin: {admin_user.is_admin}")
            
            # Verify password works
            test_password = 'admin123'
            password_valid = admin_user.check_password(test_password)
            print(f"Current password '{test_password}' valid: {password_valid}")
            
            if not password_valid:
                print("Password validation failed! Resetting password...")
                admin_user.set_password('admin123')
                db.session.commit()
                print("✓ Admin password reset")
        
        # Final verification
        print("\n=== Final Verification ===")
        verify_admin = User.query.filter_by(email='admin@durahe.com').first()
        if verify_admin:
            print(f"✓ Admin found in database")
            print(f"  Email: {verify_admin.email}")
            print(f"  Username: {verify_admin.username}")
            print(f"  Admin: {verify_admin.is_admin}")
            print(f"  Password hash: {verify_admin.password_hash[:50]}...")
            
            # Test login
            test_result = verify_admin.check_password('admin123')
            print(f"  Login test: {'✓ SUCCESS' if test_result else '✗ FAILED'}")
            
            if test_result:
                print("\n" + "="*50)
                print("✅ ADMIN LOGIN SHOULD WORK NOW!")
                print("="*50)
                print("Email: admin@durahe.com")
                print("Password: admin123")
                print("="*50)
            else:
                print("\n❌ Password verification still failing!")
                print("Please run the manual fix script.")
        else:
            print("❌ Admin not found in database!")
    
    return app