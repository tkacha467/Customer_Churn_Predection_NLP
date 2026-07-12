import pandas as pd
import os

def calculate_risk_score(processed_data_path='../data/processed/'):
    print("Calculating Final Customer Risk Scores...")
    
    # Load required datasets
    churn_pred_file = os.path.join(processed_data_path, 'churn_predictions.csv')
    nlp_file = os.path.join(processed_data_path, 'nlp_integrity_scores.csv')
    orders_file = os.path.join('../data/raw/', 'olist_orders_dataset.csv')
    customers_file = os.path.join('../data/raw/', 'olist_customers_dataset.csv')
    
    try:
        churn_df = pd.read_csv(churn_pred_file)
        nlp_df = pd.read_csv(nlp_file)
        orders = pd.read_csv(orders_file)
        customers = pd.read_csv(customers_file)
    except FileNotFoundError as e:
        print(f"Missing file: {e}")
        return None

    # Map order_id in NLP to customer_unique_id
    # order_id -> customer_id (from orders) -> customer_unique_id (from customers)
    nlp_df = nlp_df.merge(orders[['order_id', 'customer_id']], on='order_id', how='left')
    nlp_df = nlp_df.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
    
    # Calculate avg integrity score per customer
    # If they have multiple reviews, we average their integrity score.
    # integrity_score is 1.0 (good) or 0.0 (mismatch/fake)
    # We want a high score to mean HIGH RISK to align with churn_probability.
    # Actually, if integrity_score is 1.0 (perfect), the risk contribution should be 0.
    # Let's define: integrity_risk = 1.0 - integrity_score
    nlp_df['integrity_risk'] = 1.0 - nlp_df['integrity_score']
    
    customer_nlp = nlp_df.groupby('customer_unique_id')['integrity_risk'].mean().reset_index()

    # Merge churn probability and integrity risk
    final_df = churn_df.merge(customer_nlp, on='customer_unique_id', how='left')
    
    # For customers with no reviews, assume integrity_risk is 0 (innocent until proven guilty)
    final_df['integrity_risk'].fillna(0, inplace=True)
    
    # Risk Score Formula: 0.6 * churn_score + 0.4 * integrity_risk
    # Note: churn_probability is already 0 to 1 where 1 is highly likely to churn.
    final_df['risk_score'] = (0.6 * final_df['churn_probability']) + (0.4 * final_df['integrity_risk'])
    
    # Categorize Risk
    def categorize_risk(score):
        if score > 0.7:
            return 'HIGH RISK'
        elif score >= 0.4:
            return 'MEDIUM RISK'
        else:
            return 'LOW RISK'
            
    final_df['risk_category'] = final_df['risk_score'].apply(categorize_risk)
    
    # Save the final dataset
    save_file = os.path.join(processed_data_path, 'final_risk_scores.csv')
    final_df.to_csv(save_file, index=False)
    
    print(f"\nFinal Risk Scores Calculated and Saved to {save_file}")
    print(final_df['risk_category'].value_counts())
    
    return final_df

if __name__ == "__main__":
    calculate_risk_score()
