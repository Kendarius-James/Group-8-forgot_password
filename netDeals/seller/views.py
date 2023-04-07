from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from accounts.models import SellerProfile
from accounts.forms import CustomUserCreationForm, SellerUserCreationForm
from product.models import Product
from .decorators import is_seller_approved
from .forms import ProductForm
from django.shortcuts import redirect, render #redirect if user is not seller trying to do seller actions
from django.contrib import messages
from django.utils.text import slugify# Converting Title into Slug

def sellers(request):
    return render(request, 'seller/sellers.html')

#requires admin approval for sellers
def approved_sellers(request):
    sellers = SellerProfile.objects.filter(is_approved=True)
    return render(request, 'seller/approved_sellers.html', {'sellers': sellers})

def restricted_access(request):
    return render(request, 'seller/restricted_access.html')

def become_seller(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = SellerUserCreationForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role='seller'
            user.save()

            seller_profile=profile_form.save(commit=False)
            seller_profile.user = user
            seller_profile.save()

            login(request, user)
            #might need to remove seller = seller.objects.create
            #seller = seller.objects.create(email=user.email,address=user.address,phonenumber=user.phone_number,company_description=user.company_description, created_by=user)

            return redirect('core:home')
    else:
        user_form = CustomUserCreationForm()
        profile_form = SellerUserCreationForm() 

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'seller/become_seller.html', context)


@login_required
@is_seller_approved
def seller_dashboard(request):
    if request.user.role != 'seller':
        return redirect('core:home') 
    seller = request.user.sellerprofile
    products = seller.products.all()
    orders = seller.orders.all()
    for order in orders:
        order.seller_amount = 0
        order.seller_paid_amount = 0
        order.fully_paid = True

        for item in order.items.all():
            if item.seller == request.user.sellerprofile:
                if item.seller_paid:
                    order.seller_paid_amount += item.get_total_price()
                else:
                    order.seller_amount += item.get_total_price()
                    order.fully_paid = False


    return render(request, 'seller/seller_dashboard.html', {'seller': seller, 'products': products, 'orders': orders})

@login_required
@is_seller_approved
def add_product(request):
     
    if request.user.role != 'seller':
        messages.error(request, 'You do not have permission to create a product listing. Only sellers can create listings.')
        return redirect('core:home') 

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False) # Because we have not given seller yet
            product.seller = request.user.sellerprofile
            product.slug = slugify(product.title)
            product.save() #finally save

            return redirect('seller:seller-dashboard')

    else:
        form = ProductForm

    return render(request, 'seller/add_product.html', {'form': form})


@login_required
@is_seller_approved
def edit_seller(request):
    if request.user.role != 'seller':
        return redirect('core:home') 

    seller_profile = request.user.sellerprofile
    if request.method == 'POST':
        form = SellerUserCreationForm(request.POST, instance=seller_profile)
        if form.is_valid():
            form.save()
            request.user.save()
    else:
        form = SellerUserCreationForm(instance=seller_profile)

    context = {'form': form}

    return render(request, 'seller/edit_seller.html', context)

def sellers(request):
    sellers = SellerProfile.objects.all()
    return render(request, 'seller/sellers.html', {'sellers': sellers})

def seller(request, seller_id):
    seller = get_object_or_404(SellerProfile, pk=seller_id)
    return render(request, 'seller/seller.html', {'seller': seller})

