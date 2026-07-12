import Papa from 'papaparse';

/**
 * Generic CSV loader
 * @param {string} url - Path to the CSV file in public dir
 * @param {Array<string>} requiredColumns - Optional array of columns to extract
 */
export const loadCsvData = (url, requiredColumns = null) => {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        let data = results.data;
        if (requiredColumns && requiredColumns.length > 0) {
          data = data.map(row => {
            const filteredRow = {};
            requiredColumns.forEach(col => {
              if (row[col] !== undefined) {
                filteredRow[col] = row[col];
              }
            });
            return filteredRow;
          });
        }
        resolve(data);
      },
      error: (err) => {
        reject(err);
      }
    });
  });
};

/**
 * Pre-fetch all necessary datasets for the application.
 */
export const fetchAllData = async () => {
  try {
    // We specify only the required columns for each large CSV to save memory.
    const [riskScores, churnPredictions, integrityScores, rfmFeatures] = await Promise.all([
      loadCsvData('/data/final_risk_scores.csv', ['customer_unique_id', 'risk_score', 'risk_category', 'monetary', 'churn']),
      loadCsvData('/data/churn_predictions_full.csv', ['customer_unique_id', 'churn_actual', 'churn_predicted', 'churn_probability']),
      loadCsvData('/data/customer_integrity.csv', ['customer_unique_id', 'avg_integrity_score', 'has_mismatch']),
      loadCsvData('/data/rfm_features.csv', [
        'customer_unique_id', 'recency', 'frequency', 'monetary', 'avg_review_score', 
        'avg_freight_value', 'avg_installments', 'avg_delivery_delay'
      ]),
    ]);

    return {
      riskScores,
      churnPredictions,
      integrityScores,
      rfmFeatures
    };
  } catch (error) {
    console.error("Error loading CSV data:", error);
    throw error;
  }
};
