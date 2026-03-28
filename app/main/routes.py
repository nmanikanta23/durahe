from flask import render_template, request, jsonify, current_app
from app.main import main
from app.models import Product, Category
import os

@main.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', 
                         featured_products=featured_products,
                         categories=categories)

@main.route('/products')
def products():
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '')
    
    if category_id:
        products = Product.query.filter_by(category_id=category_id, is_active=True).all()
    elif search_query:
        products = Product.query.filter(
            Product.name.contains(search_query) | Product.description.contains(search_query),
            Product.is_active == True
        ).all()
    else:
        products = Product.query.filter_by(is_active=True).all()
    
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories, search_query=search_query)

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@main.route('/cart/count')
def cart_count():
    from flask_login import current_user
    if current_user.is_authenticated:
        count = sum(item.quantity for item in current_user.cart_items)
        return jsonify({'count': count})
    return jsonify({'count': 0})