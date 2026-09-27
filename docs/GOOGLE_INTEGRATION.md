# Google Integration & Compliance Specification

## 1. Compliance Principles
Google's Business Profile Review Policies explicitly require:
1. **Genuine Human Authorship**: Reviews must reflect a real customer's genuine experience.
2. **Prohibition of Automated / Fake Submissions**: Systems must NOT automatically post reviews to Google via automated scripts, bot accounts, or unauthorized endpoints.
3. **Prohibition of Review Gating**: Businesses must NOT selectively solicit positive reviews or divert negative reviews away from public review sites.

---

## 2. ChurnLens Google Workflow
ChurnLens complies 100% with Google's guidelines:

```
Customer selects rating (1 to 5 Stars)
                  │
Customer selects topics & picks review idea
                  │
Customer personalizes / edits review
                  │
Customer approves text
                  │
[ ⭐ Copy & Continue to Google ]
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
Review copied to      Official Google Review link
clipboard             opens in new browser tab
                             │
                             ▼
              Customer pastes and submits
                their review on Google
```

- **Customer Remains the Author**: The customer approves the wording, copies the review, and performs the final submission directly on Google.
- **Zero Rating-Based Review Gating**: Customers who rate 1, 2, 3, 4, or 5 stars have the exact same access to the Google review destination. An optional private feedback link is available for direct notes to management without gating or blocking Google.
- **No Deceptive Claims**: ChurnLens never claims "1-click automatic posting". The button clearly reads: `Copy & Continue to Google`.

---

## 3. Google Review Link Configuration
The restaurant owner pastes their official review link:
- Example format: `https://g.page/r/{BUSINESS_ID}/review` or `https://search.google.com/local/writereview?placeid={PLACE_ID}`.
- ChurnLens provides a built-in `[ Test Link ↗ ]` button allowing owners to verify that the destination opens the review composer on Google Maps.

---

## 4. Future Google Business Profile API Integration (Owner Only)
Google Business Profile APIs support OAuth 2.0 authorized access for verified business owners:
- Listing and reading existing Google reviews.
- Replying directly to customer reviews as the business owner.
- *Note*: Google APIs do **not** support posting customer reviews on behalf of other users. Any future Google integration in ChurnLens will focus strictly on owner reply automation.
