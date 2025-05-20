import pandas as pd
import logging
from surprise import Dataset, Reader, SVD, KNNWithMeans, AlgoBase
from surprise.model_selection import train_test_split
from surprise import accuracy


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    A class for training a recommendation model and generating recommendations.
    """

    def __init__(
        self,
        model_type: str = "svd",
        min_ratings_per_user: int = 5,
        rating_scale: tuple = (1, 5),
        item_id_col: str = "isbn13",
        user_id_col: str = "user_id",
        rating_col: str = "rate",
        svd_n_factors: int = 100,
        knn_k: int = 40,
        random_state: int = 42,
    ):
        """
        Initializes the RecommendationEngine.

        Args:
            model_type (str): Type of model to use ('svd' or 'knn').
            min_ratings_per_user (int): Minimum number of ratings a user must have to be included.
            rating_scale (tuple): The scale of ratings (min_rating, max_rating).
            item_id_col (str): Name of the column for item IDs in the input DataFrame.
            user_id_col (str): Name of the column for user IDs in the input DataFrame.
            rating_col (str): Name of the column for ratings in the input DataFrame.
            svd_n_factors (int): Number of factors for SVD.
            knn_k (int): Number of neighbors for KNN.
            random_state (int): Random state for reproducibility.
        """
        self.model_type = model_type.lower()
        self.min_ratings_per_user = min_ratings_per_user
        self.rating_scale = rating_scale
        self.item_id_col = item_id_col
        self.user_id_col = user_id_col
        self.rating_col = rating_col
        self.svd_n_factors = svd_n_factors
        self.knn_k = knn_k
        self.random_state = random_state

        self.model: AlgoBase | None = None
        self.trainset = None  # Surprise trainset object
        self.full_ratings_df = None  # To store the original df for all items

        if self.model_type == "svd":
            self.model = SVD(
                n_factors=self.svd_n_factors, random_state=self.random_state
            )
        elif self.model_type == "knn":
            # Using pearson_baseline similarity as it often performs well
            sim_options = {"name": "pearson_baseline", "user_based": True}
            self.model = KNNWithMeans(k=self.knn_k, sim_options=sim_options)
        else:
            raise ValueError(
                f"Unsupported model type: {model_type}. Choose 'svd' or 'knn'."
            )
        logger.info(
            f"RecommendationEngine initialized with model type: {self.model_type.upper()}"
        )

    def _filter_active_users(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filters out users with less than a minimum number of ratings.
        Private helper method.
        """
        logger.info(
            f"Filtering users with less than {self.min_ratings_per_user} ratings."
        )
        user_counts = ratings_df[self.user_id_col].value_counts()
        active_users = user_counts[user_counts >= self.min_ratings_per_user].index
        filtered_df = ratings_df[ratings_df[self.user_id_col].isin(active_users)]

        if filtered_df.empty:
            logger.warning("DataFrame is empty after filtering active users.")
        else:
            logger.info(
                f"Users before filtering: {len(user_counts)}. Users after filtering: {len(active_users)}. Ratings remaining: {len(filtered_df)}"
            )
        return filtered_df

    def _create_surprise_dataset(self, ratings_df: pd.DataFrame) -> Dataset | None:
        """
        Creates a Surprise Dataset object from a pandas DataFrame.
        Private helper method.
        """
        if ratings_df.empty:
            logger.error("Cannot create Surprise dataset from an empty DataFrame.")
            return None
        logger.info(f"Creating Surprise Dataset with scale {self.rating_scale}.")
        reader = Reader(rating_scale=self.rating_scale)
        try:
            data = Dataset.load_from_df(
                ratings_df[[self.user_id_col, self.item_id_col, self.rating_col]],
                reader,
            )
            return data
        except Exception as e:
            logger.error(f"Error creating Surprise dataset: {e}")
            return None

    def _evaluate_model(self, testset: Dataset):
        logger.info("Evaluating model on the test set...")
        predictions = self.model.test(testset)
        rmse = accuracy.rmse(predictions, verbose=False)
        mae = accuracy.mae(predictions, verbose=False)
        logger.info(f"Evaluation - RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        return {"rmse": rmse, "mae": mae}

    def train(self, ratings_df: pd.DataFrame, test_size: float = 0.2) -> dict | None:
        """
        Trains the recommendation model.

        Args:
            ratings_df (pd.DataFrame): DataFrame with user ratings.
                                      Must contain columns specified by user_id_col, item_id_col, and rating_col.
            test_size (float): Proportion of the dataset to include in the test split.

        Returns:
            dict: A dictionary containing RMSE and MAE if test_size > 0, else None.
                 Returns None if training failed.
        """
        if not isinstance(ratings_df, pd.DataFrame):
            logger.error("ratings_df must be a pandas DataFrame.")
            return None

        if not all(
            col in ratings_df.columns
            for col in [self.user_id_col, self.item_id_col, self.rating_col]
        ):
            logger.error(
                f"ratings_df must contain columns: {self.user_id_col}, {self.item_id_col}, {self.rating_col}"
            )
            return None

        self.full_ratings_df = (
            ratings_df.copy()
        )  # Store for generating recommendations later

        logger.info("Starting model training process...")
        filtered_ratings = self._filter_active_users(self.full_ratings_df)

        if filtered_ratings.empty:
            logger.error(
                "No data available after filtering active users. Training aborted."
            )
            return None

        dataset = self._create_surprise_dataset(filtered_ratings)
        if dataset is None:
            logger.error("Failed to create Surprise dataset. Training aborted.")
            return None

        logger.info("Splitting data into training and testing sets.")
        try:
            self.trainset, testset = train_test_split(
                dataset, test_size=test_size, random_state=self.random_state
            )
        except ValueError as e:  # Handles cases where dataset is too small for split
            logger.warning(
                f"Could not split dataset (test_size={test_size}): {e}. Using full dataset for training."
            )
            self.trainset = dataset.build_full_trainset()
            testset = None

        if self.model is None:  # Should have been initialized in __init__
            logger.error("Model is not initialized. Training aborted.")
            return None

        logger.info(f"Training {self.model_type.upper()} model...")
        self.model.fit(self.trainset)
        logger.info("Model training complete.")

        # FIX: Return the evaluation metrics
        if testset:
            metrics = self._evaluate_model(testset)
            return metrics
        else:
            logger.warning("No test set available for evaluation.")
            return {"rmse": None, "mae": None}

    def recommend_for_user(
        self, user_id: object, n_recommendations: int = 10
    ) -> list[tuple[object, float]]:
        """
        Generates top-N recommendations for a specific user for items they haven't rated.

        Args:
            user_id (object): The ID of the user for whom to generate recommendations.
                             This should be the raw user ID from your original data.
            n_recommendations (int): The number of recommendations to return.

        Returns:
            list[tuple[object, float]]: A list of (item_id, estimated_rating) tuples,
                                       sorted by estimated rating in descending order.
                                       Returns an empty list if the model is not trained,
                                       user is not found, or no unrated items are found.
        """
        if not self.model or not self.trainset:
            logger.error(
                "Model has not been trained yet or trainset is missing. Please call the 'train' method first."
            )
            return []
        if self.full_ratings_df is None:
            logger.error(
                "Full ratings data is not available. Call 'train' method first."
            )
            return []

        logger.info(
            f"Generating {n_recommendations} recommendations for user_id '{user_id}'."
        )

        try:
            # Convert the raw user_id to Surprise's inner id.
            user_inner_id = self.trainset.to_inner_uid(user_id)
        except ValueError:
            logger.warning(
                f"User_id '{user_id}' not found in the training set (after filtering). Cannot generate recommendations with current model context."
            )
            # Alternative: Could try to predict even if user not in trainset (cold start, model dependent)
            # For now, returning empty as per original notebook's behavior for unknown users in trainset.
            return []

        # Get all item inner IDs
        all_items_inner_ids = list(self.trainset.all_items())

        # Get items the user has already rated (inner IDs)
        # train_set.ur is a dictionary where keys are inner user IDs
        # and values are lists of (inner_item_id, rating) tuples.
        rated_items_inner_ids = {
            inner_iid for (inner_iid, _) in self.trainset.ur[user_inner_id]
        }

        # Identify items the user has NOT rated
        unrated_items_inner_ids = [
            inner_iid
            for inner_iid in all_items_inner_ids
            if inner_iid not in rated_items_inner_ids
        ]

        if not unrated_items_inner_ids:
            logger.info(
                f"User '{user_id}' has rated all available items or no unrated items found."
            )
            return []

        # Predict ratings for unrated items
        predictions_for_user = []
        for inner_item_id in unrated_items_inner_ids:
            # Convert inner item ID back to raw item ID for prediction
            raw_item_id = self.trainset.to_raw_iid(inner_item_id)
            # The model's predict method takes raw user and item IDs
            prediction = self.model.predict(uid=user_id, iid=raw_item_id)
            predictions_for_user.append((raw_item_id, prediction.est))

        # Sort predictions by estimated rating in descending order
        predictions_for_user.sort(key=lambda x: x[1], reverse=True)

        # Return the top N recommendations
        top_n_recs = predictions_for_user[:n_recommendations]
        logger.info(
            f"Successfully generated {len(top_n_recs)} recommendations for user '{user_id}'."
        )
        return top_n_recs


if __name__ == "__main__":
    # Create a dummy ratings DataFrame for demonstration
    # In a real scenario, you would load your 'user_ratings.csv'
    data = {
        "user_id": [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5],
        "isbn13": [
            "A",
            "B",
            "C",
            "A",
            "D",
            "E",
            "F",
            "B",
            "C",
            "D",
            "E",
            "G",
            "A",
            "H",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
        ],
        "rate": [5, 4, 3, 5, 2, 5, 4, 4, 3, 2, 5, 4, 1, 5, 5, 5, 5, 3, 2, 1],
    }
    ratings_df = pd.DataFrame(data)

    # --- SVD Example ---
    print("\n--- SVD Model Example ---")
    # Initialize RecommendationEngine with SVD model
    engine_svd = RecommendationEngine(
        model_type="svd", min_ratings_per_user=2, rating_scale=(1, 5)
    )

    # Train the model
    # Using a smaller test_size for this small dummy dataset
    eval_metrics_svd = engine_svd.train(ratings_df, test_size=0.2)
    if eval_metrics_svd:
        print(
            f"SVD Model Evaluation: RMSE={eval_metrics_svd['rmse']:.4f}, MAE={eval_metrics_svd['mae']:.4f}"
        )

    # Get recommendations for a user
    user_to_recommend = 1
    if engine_svd.model:  # Check if model was trained
        recommendations_svd = engine_svd.recommend_for_user(
            user_id=user_to_recommend, n_recommendations=3
        )
        print(
            f"Top 3 SVD recommendations for user {user_to_recommend}: {recommendations_svd}"
        )

        # Example for a user who might not be in trainset or has few ratings
        user_to_recommend_new = 6  # This user is not in the training data
        recommendations_new_user_svd = engine_svd.recommend_for_user(
            user_id=user_to_recommend_new, n_recommendations=3
        )
        print(
            f"Top 3 SVD recommendations for new user {user_to_recommend_new}: {recommendations_new_user_svd}"
        )  # Expected to be empty or based on global averages if model supports

        user_with_few_ratings = 4  # This user has 2 ratings, might be filtered if min_ratings_per_user was higher
        recommendations_user4_svd = engine_svd.recommend_for_user(
            user_id=user_with_few_ratings, n_recommendations=3
        )
        print(
            f"Top 3 SVD recommendations for user {user_with_few_ratings}: {recommendations_user4_svd}"
        )

    # --- KNN Example ---
    print("\n--- KNN Model Example ---")
    engine_knn = RecommendationEngine(
        model_type="knn", min_ratings_per_user=2, rating_scale=(1, 5), knn_k=2
    )  # Small k for tiny dataset

    eval_metrics_knn = engine_knn.train(ratings_df, test_size=0.2)
    if eval_metrics_knn:
        print(
            f"KNN Model Evaluation: RMSE={eval_metrics_knn['rmse']:.4f}, MAE={eval_metrics_knn['mae']:.4f}"
        )

    if engine_knn.model:
        recommendations_knn = engine_knn.recommend_for_user(
            user_id=user_to_recommend, n_recommendations=3
        )
        print(
            f"Top 3 KNN recommendations for user {user_to_recommend}: {recommendations_knn}"
        )