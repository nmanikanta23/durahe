from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderItem, CartItem, Product
from app.forms import CheckoutForm
from datetime import datetime
import uuid
from app.orders import orders

@orders.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('main.products'))
    
    # Check stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            flash(f'{item.product.name} has only {item.product.stock} items in stock. Please update your cart.', 'danger')
            return redirect(url_for('cart.view_cart'))
    
    total = sum(item.product.final_price * item.quantity for item in cart_items)
    
    form = CheckoutForm()
    
    if request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.pincode.data = current_user.pincode
    
    if form.validate_on_submit():
        # Create order
        order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total,
            payment_method=form.payment_method.data,
            shipping_address=form.address.data,
            shipping_city=form.city.data,
            shipping_state=form.state.data,
            shipping_pincode=form.pincode.data,
            phone=form.phone.data,
            notes=form.full_name.data
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Create order items and update stock
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                product_price=cart_item.product.final_price,
                quantity=cart_item.quantity,
                total_price=cart_item.product.final_price * cart_item.quantity
            )
            db.session.add(order_item)
            
            # Update stock
            cart_item.product.stock -= cart_item.quantity
        
        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        
        # Update user information
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.state = form.state.data
        current_user.pincode = form.pincode.data
        
        db.session.commit()
        
        flash(f'Order placed successfully! Order Number: {order_number}', 'success')
        return redirect(url_for('orders.order_confirmation', order_id=order.id))
    
    return render_template('orders/checkout.html', form=form, cart_items=cart_items, total=total)

@orders.route('/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('orders/confirmation.html', order=order)

@orders.route('/history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/history.html', orders=orders)

@orders.route('/payment/<int:order_id>')
@login_required
def payment_page(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('orders/payment.html', order=order)