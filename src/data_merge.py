import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

def merge_data(raw_data_path='../data/raw/', save_path='../data/processed/'):
    print("Starting Data Merge Process...")
    
    # Load all tables
    print("Loading tables...")
    try:
        customers   = pd.read_csv(os.path.join(raw_data_path, 'olist_customers_dataset.csv'))
        orders      = pd.read_csv(os.path.join(raw_data_path, 'olist_orders_dataset.csv'))
        order_items = pd.read_csv(os.path.join(raw_data_path, 'olist_order_items_dataset.csv'))
        payments    = pd.read_csv(os.path.join(raw_data_path, 'olist_order_payments_dataset.csv'))
        reviews     = pd.read_csv(os.path.join(raw_data_path, 'olist_order_reviews_dataset.csv'))
        products    = pd.read_csv(os.path.join(raw_data_path, 'olist_products_dataset.csv'))
        sellers     = pd.read_csv(os.path.join(raw_data_path, 'olist_sellers_dataset.csv'))
        geo         = pd.read_csv(os.path.join(raw_data_path, 'olist_geolocation_dataset.csv'))
        category    = pd.read_csv(os.path.join(raw_data_path, 'product_category_name_translation.csv'))
    except FileNotFoundError as e:
        print(f"Error loading files: {e}. Please ensure data is in {raw_data_path}")
        return None

    # Merge chain exactly as specified:
    # order_items -> products -> category_translation -> orders -> reviews -> payments -> customers -> sellers -> geolocation
    
    print("Merging tables...")
    # 1. order_items -> products
    df = order_items.merge(products, on='product_id', how='left')
    
    # 2. -> category_translation
    df = df.merge(category, on='product_category_name', how='left')
    
    # 3. -> orders
    df = df.merge(orders, on='order_id', how='left')
    
    # 4. -> reviews
    df = df.merge(reviews, on='order_id', how='left')
    
    # 5. -> payments
    df = df.merge(payments, on='order_id', how='left')
    
    # 6. -> customers
    df = df.merge(customers, on='customer_id', how='left')
    
    # 7. -> sellers
    df = df.merge(sellers, on='seller_id', how='left')
    
    # 8. -> geolocation (approximated on zip code for seller or customer, let's join on customer zip code prefix)
    # The spec just says JOIN geolocation ON zip_code_prefix. We'll join on customer_zip_code_prefix to get customer location.
    geo_unique = geo.drop_duplicates(subset=['geolocation_zip_code_prefix'])
    df = df.merge(geo_unique, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
    
    print("Handling missing values & data issues...")
    # Fix nulls in category name
    df['product_category_name_english'].fillna('unknown', inplace=True)
    
    # Hardcode the 3 untranslated categories as per spec
    translations = {
        'pc_gamer': 'pc_gamer',
        'portateis_cozinha_e_preparadores_de_alimentos': 'kitchen_and_food_preparators'
    }
    df['product_category_name_english'] = df.apply(
        lambda row: translations.get(row['product_category_name'], row['product_category_name_english']) 
        if pd.isna(row['product_category_name_english']) or row['product_category_name_english'] == 'unknown' 
        else row['product_category_name_english'], 
        axis=1
    )
    
    # Fill review text missing values with placeholders
    df['review_comment_message'].fillna('no_text', inplace=True)
    df['review_comment_title'].fillna('no_title', inplace=True)
    
    # Ensure processed directory exists
    os.makedirs(save_path, exist_ok=True)
    
    # Save processed data
    save_file = os.path.join(save_path, 'olist_cleaned.csv')
    df.to_csv(save_file, index=False)
    print(f"Merge complete! Final dataset saved to {save_file}. Shape: {df.shape}")
    
    return df

if __name__ == "__main__":
    # Ensure paths are correct when run directly from src/
    merge_data(raw_data_path='../data/raw/', save_path='../data/processed/')
