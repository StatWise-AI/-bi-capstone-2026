# How the Machine Learning Notebook Works: A Plain-Language Walkthrough

This document explains `Stockout_Risk_Classification.ipynb` cell by cell, in plain English, for someone presenting it who does not have a machine learning background. Read this alongside the notebook: open the notebook, and for each section, use the matching explanation below to describe what is happening and, more importantly, why.

---

## 1. The Big Picture, Before Any Code

**The problem:** the dashboard already tells us that 194 products are "High Risk" of running out of stock. But that label was handed to us in the data. The real question a business would ask next is: **could we predict that label ourselves, using only the everyday operational numbers (stock levels, demand, lead times, cost), before a human or a pre-built score tells us?**

That is what a **classification model** is: a program that looks at a set of known facts about something (here, a product) and predicts which category it belongs to, out of a fixed list of categories (here: High Risk, Medium Risk, or Low Risk). It is called "classification" specifically because we are sorting things into named buckets, not predicting a number (predicting a number would be called "regression").

**Why go to this trouble at all?** Two reasons worth saying out loud to a teacher:
1. If a model can learn the pattern from ordinary operational data, the business could apply the same logic to a **brand-new product** that has no history yet, which the original pre-computed Risk Score cannot do (a new product does not have a Risk_Score assigned to it).
2. It tells us **which factors matter most** for risk (Step 7 below), which is useful insight even beyond the prediction itself.

**The general recipe:** every practical ML project, regardless of what it predicts, follows roughly the same sequence of steps, and the notebook follows it in order:
1. Look at the data before touching any model (EDA).
2. Engineer any extra features that domain knowledge suggests would help.
3. Clean and prepare the data so a model can actually consume it.
4. Try several candidate models rather than committing to one blindly.
5. Train the most promising one properly.
6. Test it honestly, on data it has never seen.
7. Ask what the model actually learned.
8. Check whether it's good enough to be useful for the original business goal.

Everything below maps one of these steps to the exact cells in the notebook.

---

## 2. Step 0: Loading the Data (cells 1 to 3)

The first code cell just imports the toolkits we need (pandas for tables, matplotlib/seaborn for charts, scikit-learn for the actual ML algorithms, xgboost for one extra algorithm). Nothing clever happens here, it's the equivalent of laying out your tools before starting work.

The next cell loads the same `Stock_Dynamics_Dataset.xlsx` file that feeds the Power BI dashboard, so **the notebook and the dashboard are looking at the exact same 500 rows.** This matters for the presentation: it means whatever the model finds is directly comparable to what's on the dashboard, not some separate disconnected dataset.

---

## 3. Step 1: Exploratory Data Analysis, "EDA" (cells 5 to 9)

**Why do this before building anything?** Because building a model on data you haven't looked at is like a doctor prescribing medicine without examining the patient. A few minutes of looking prevents hours of confusion later.

- `df.info()` and `df.describe()`: a basic health check. Are there missing values? Are the numbers in a sensible range? (For example, confirming Service Level is stored as 75 to 95, not 0.75 to 0.95, avoids a scaling mistake later.)
- **Class balance chart:** shows how many products fall into each of the three risk categories (194 High, 177 Medium, 129 Low). This matters a lot: if one category had only 5 products out of 500, the model could get "good" accuracy just by ignoring that tiny category entirely and still being right most of the time, which would be a useless model in practice. Here the three groups are close enough in size that this is not a serious problem, which is itself worth reporting as a finding.
- **Risk Score by category boxplot:** a sanity check to see whether risk visibly differs by product category, using the Risk_Score column that will NOT be used as a model input (see Step 3 for why). This is just confirming that risk isn't random, that there is a real signal in the data for a model to find.
- **Correlation heatmap:** shows which numeric columns tend to move together (for example, does higher demand volatility go with lower service level?). This gives an early hint about which features might turn out to matter, before the model itself confirms it in Step 7.

---

## 4. Step 2: Feature Engineering (cells 11)

"Feature engineering" simply means **creating new, more useful columns out of the columns you already have**, using domain knowledge about what actually matters for the problem.

Two new columns are created here, both suggested directly by the dataset's own documentation sheet:
- **Stock_to_Reorder_Ratio** = current stock divided by the reorder point. A raw "Current_Stock_Level" number means nothing on its own (is 300 units a lot or a little?), but a *ratio* below 1 immediately and universally means "this product is already below the point where it should have been reordered", regardless of what kind of product it is. That is a much more directly useful signal than the raw stock number.
- **Demand_Volatility_Index** = demand's variability divided by its average level. This turns "the demand numbers wiggle by X units" into "the demand is unpredictable relative to how much of it there typically is", which is a fairer way to compare a slow-moving product to a fast-moving one.

**Why does this step matter for the presentation?** It shows the model isn't just being fed raw numbers blindly, real business logic ("what would actually make a product risky?") was built into the inputs before the model ever saw them. This is often what separates a mediocre model from a good one, more than the choice of algorithm does.

---

## 5. Step 3: Data Preprocessing (cells 13 to 16)

This step turns the cleaned, human-readable table into the strict numeric format that ML algorithms require, and makes two deliberate, explainable decisions along the way.

### 5.1 The most important decision in the whole notebook: avoiding "data leakage"

The dataset's documentation sheet groups `Risk_Score` and `Current_Stock_Coverage_Days` together with the target we're trying to predict, under the heading "Risk Indicators". `Risk_Score` is explicitly described as "a composite score based on multiple risk factors", which is a strong hint that the High/Medium/Low label was directly calculated FROM Risk_Score using fixed cutoffs (this matches the dashboard's own decision framework: score 60+ is High Risk, 35 to 60 is Medium, below 35 is Low).

If we let the model see Risk_Score, it would not really be learning anything, it would just be learning the cutoff rule (which anyone could write in one line of code, without any machine learning at all). Worse, it would report a suspiciously perfect-looking accuracy that would completely fall apart on a new product that doesn't have a Risk_Score yet. This mistake has a name in the ML field: **data leakage**, meaning information about the answer "leaks" into the inputs. Explicitly catching and avoiding this is a sign of a properly done analysis, and is worth stating plainly in the presentation: **"we deliberately excluded the columns that would let the model cheat."**

For the same underlying reason (a new product also doesn't have a Supplier history or its own ID yet in any meaningful predictive sense), `SKU_ID` and `Supplier_ID` are also excluded, they are just labels/identifiers, not real business characteristics that would generalize to a different product.

What's left is exactly the 25 real, ordinary operational columns the documentation sheet describes as the intended features: product info, stock levels, demand patterns, historical performance, and operational cost metrics, plus the 2 engineered features from Step 2.

### 5.2 Turning categories into numbers: one-hot encoding

Columns like `Product_Category` ("Electronics", "Apparel", ...) are words, but the math underneath a model only understands numbers. **One-hot encoding** turns one "Product_Category" column into eight new columns, one per category, each containing a 1 if the product belongs to that category and a 0 otherwise. This lets the model use category information without ever assuming a false order between categories (it would be wrong to say "Electronics" is somehow mathematically "more" than "Apparel", so we don't encode it as a single ranked number).

### 5.3 Splitting into training data and test data

The data is split 70% / 30%: 70% of products are used to teach the model, and the remaining 30% are held back and never shown to the model during training. Why do this at all? **Because the only fair way to know if a model actually learned something useful, rather than just memorized the training examples, is to test it on examples it has never seen.** This is the single most important safeguard against a model that looks great on paper but fails in the real world; it's the ML equivalent of not letting a student see the exam questions before the exam.

The split is "stratified", meaning each of the three risk categories keeps roughly the same proportion in both the training set and the test set, so the test isn't accidentally testing on a lopsided sample.

### 5.4 Scaling the numbers

`Avg_Daily_Demand` might range in the tens, while `Total_Storage_Space` ranges in the thousands. Some algorithms (specifically Logistic Regression, one of our four candidates) can be thrown off by that size difference, treating the bigger numbers as automatically more important just because they're bigger. Scaling rewrites every numeric column onto the same comparable scale, so no column gets an unfair head start purely due to its units. Tree-based models (Decision Tree, Random Forest, XGBoost) don't have this problem, so scaling is applied only where it's actually needed.

---

## 6. Step 4 and 5: Choosing and Training a Model (cells 18 to 21)

### 6.1 Why try four different models instead of picking one?

Nobody can know in advance which algorithm will fit a particular dataset best, so the responsible approach is to race a small, deliberately varied field of candidates and let the data decide. Here's what each one is, in plain terms:

- **Logistic Regression**: the simplest of the four. It essentially draws straight dividing lines between the risk categories based on weighted combinations of the inputs. Fast, easy to explain, and a good baseline: if a fancier model can't beat this, the fancier model isn't worth the extra complexity.
- **Decision Tree**: makes a series of yes/no splits, like a flowchart ("Is Lead_Time_Days over 20? If yes, is Demand_Volatility over 0.3?..."), ending in a risk label. Easy for a human to follow step by step, but a single tree can be a bit unstable (small data changes can reshape it a lot).
- **Random Forest**: instead of one decision tree, it builds a large number of slightly different trees (each seeing a random subset of the data and features) and lets them vote on the final answer. This "wisdom of crowds" approach is usually more accurate and more stable than any single tree.
- **XGBoost**: a more advanced relative of Random Forest. Instead of building all its trees independently, each new tree specifically focuses on fixing the mistakes the previous trees made. It's often the strongest performer on exactly this kind of structured, spreadsheet-style business data, which is why it's included as the most sophisticated candidate.

### 6.2 Why cross-validation instead of a single test?

Before even touching the held-out 30% test set, the four candidates are compared using **5-fold cross-validation**: the training data is split into 5 chunks, and each model is trained 5 times, each time using a different chunk as a temporary check while training on the other four. The results are then averaged. Why bother with this extra step? **A single lucky or unlucky split of the data could make a mediocre model look great, or a good model look bad, purely by chance.** Averaging over 5 different splits gives a far more trustworthy comparison before we commit to a "final" model. In this run, the four models scored close to each other (roughly 76.6% to 80.3% average accuracy), with XGBoost narrowly ahead.

### 6.3 Why tune the model afterward?

Random Forest was carried forward and tuned further using `GridSearchCV`, which systematically tries a grid of different setting combinations (for example: how many trees to build, how deep each tree is allowed to grow) and keeps the combination that scores best under the same 5-fold cross-validation process. This is the difference between using an algorithm "out of the box" and actually adjusting its settings for this specific dataset, similar to adjusting the settings on a camera for the specific lighting in a room rather than always using the default.

---

## 7. Step 6: Honest Evaluation on Data the Model Has Never Seen (cells 23 to 24)

This is the moment of truth: the tuned model is finally shown the 30% test set it has never touched, and we measure how it does. A few terms worth explaining simply:

- **Accuracy**: out of all the test predictions, what percentage were exactly correct? The model scored **80.7%** here, meaning it got about 4 out of every 5 products' risk category right on data it had never seen before.
- **Precision** (for a given category, say "High Risk"): out of everything the model *called* High Risk, what percentage actually were? High precision means few false alarms.
- **Recall** (for a given category): out of everything that *actually was* High Risk, what percentage did the model correctly catch? High recall means few missed cases.
- **Why both matter, and why they can trade off against each other**: a model that labels *everything* as High Risk would have perfect recall (it never misses a real one) but terrible precision (constant false alarms). A model that only ever labels the single most obvious case as High Risk might have perfect precision but terrible recall (it misses almost everyone who's actually at risk). A good model needs a healthy balance of both, which is exactly why the business brief (Step 8) asks for both, with different thresholds for each.
- **The confusion matrix**: a simple grid showing exactly which categories get confused with which. It's the most direct way to see, for example, that Medium Risk products are the ones most often mistaken for something else, which turned out to be true here.

---

## 8. Step 7: Which Features Actually Matter (cells 26)

Once a tree-based model like Random Forest is trained, it can report exactly how much each input feature contributed to its decisions, ranked from most to least important. This step produces a bar chart of the top 15 most influential features.

**Why present this at all, beyond the prediction itself?** Because it converts the model from a black box into a source of business insight: it tells the business *which levers actually move the needle on stockout risk* (for example, if Lead_Time_Days or the engineered Stock_to_Reorder_Ratio come out near the top, that's a concrete, actionable finding, not just an abstract accuracy number). This is arguably the most presentable part of the whole notebook, since it connects directly back to decisions a manager could make.

---

## 9. Step 8: Did It Actually Meet the Business's Own Bar? (cells 28 to 29)

The documentation sheet doesn't just ask for "a good model", it states specific numeric success targets:
- Overall accuracy above 85%
- Precision for the High Risk class above 80% (don't cry wolf too often)
- Recall for the High Risk class above 90% (don't miss the real emergencies, since missing one is more costly than a false alarm)

The notebook checks the tuned model against each of these three targets explicitly and prints a plain "did it pass" verdict for each, rather than leaving anyone to guess. The honest result:
- Overall accuracy: **80.7%**, short of the 85% target.
- High Risk precision: **89.7%**, clears the 80% target comfortably.
- High Risk recall: **89.7%**, just short of the 90% target, by three tenths of a point.

**How to present this to a teacher:** resist the temptation to only mention the wins. The honest, well-rounded story is: *"the model is genuinely strong exactly where it matters most, catching and correctly flagging the highest-stakes High Risk products, even though its overall accuracy falls a bit short of the target, mainly because it struggles to tell Medium Risk products apart from the other two categories."* That is a real, specific, defensible finding, and it's a far more credible presentation than simply claiming success across the board.

---

## 10. A Short Glossary, for Quick Reference During Questions

| Term | Plain-English meaning |
|---|---|
| Classification | Sorting things into a fixed set of named categories (here: High/Medium/Low Risk) |
| Feature | An input column the model is allowed to use to make its prediction |
| Target / Label | The answer the model is trying to predict (here: Stockout_Risk_Category) |
| Data leakage | Accidentally letting a feature contain information that gives away the answer |
| Training data | The examples the model is allowed to learn from |
| Test data | The examples held back purely to check how well the model actually learned |
| Overfitting | A model that memorized the training examples instead of learning a general pattern, so it does great on training data and poorly on new data |
| Cross-validation | Repeating the train/check process on several different slices of the training data, then averaging, for a more trustworthy comparison |
| Hyperparameter tuning | Systematically trying different algorithm settings to find the best-performing combination |
| Accuracy | Percent of all predictions that were exactly correct |
| Precision | Of everything predicted as category X, what percent really was X (false-alarm control) |
| Recall | Of everything that really was category X, what percent did the model catch (missed-case control) |
| Confusion matrix | A grid showing exactly which categories the model mixes up with which |
| Feature importance | A ranking of which input columns most influenced the model's decisions |

---

## 11. Suggested Presentation Flow

If walking a teacher through this live, a natural order is:
1. State the business question in one sentence (Section 1 above).
2. Show the class balance chart (Step 1), to establish the data is reasonably balanced.
3. Explain the data leakage decision (Step 3) as the single most important design choice, it shows judgment, not just following instructions.
4. Show the cross-validation comparison chart (Step 4/5), explaining that four different approaches were raced fairly before picking one.
5. Show the confusion matrix and the classification report (Step 6).
6. Show the feature importance chart (Step 7) as the "so what does this actually tell the business" moment.
7. End on the business validation table (Step 8), stating both what was achieved and what fell short, honestly.
