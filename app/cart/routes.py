from flask import render_template, redirect, url_for, flash, request, Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import CartItem, Product
from app.cart import cart

@cart.route('/')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.final_price * item.quantity for item in cart_items)
    return render_template('cart/cart.html', cart_items=cart_items, total=total)

@cart.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.stock:
        flash(f'Sorry, only {product.stock} items available in stock.', 'warning')
        return redirect(request.referrer or url_for('main.product_detail', product_id=product_id))
    
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    if cart_item:
        if cart_item.quantity + quantity > product.stock:
            flash(f'Cannot add more than {product.stock} items.', 'warning')
        else:
            cart_item.quantity += quantity
            flash(f'{product.name} quantity updated in cart!', 'success')
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
        flash(f'{product.name} added to cart!', 'success')
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Added to cart'})
    
    return redirect(url_for('cart.view_cart'))

@cart.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0 and quantity <= cart_item.product.stock:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated successfully!', 'success')
    elif quantity <= 0:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
    else:
        flash(f'Only {cart_item.product.stock} items available.', 'warning')
    
    return redirect(url_for('cart.view_cart'))

@cart.route('/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
    else:
        flash('Unauthorized action.', 'danger')
    
    return redirect(url_for('cart.view_cart'))