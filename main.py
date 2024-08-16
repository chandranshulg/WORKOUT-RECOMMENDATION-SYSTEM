import random
import sqlite3
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('workout_recommendations.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    fitness_level TEXT,
                    goal TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    workout_type TEXT,
                    workout_name TEXT,
                    feedback INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')

conn.commit()

# Define workout data
workouts = {
    'Cardio': ['Running', 'Cycling', 'Jump Rope', 'Rowing', 'Swimming'],
    'Strength Training': ['Push-ups', 'Squats', 'Deadlifts', 'Bench Press', 'Pull-ups'],
    'Yoga': ['Sun Salutation', 'Tree Pose', 'Downward Dog', 'Warrior Pose', 'Child\'s Pose']
}

fitness_levels = ['Beginner', 'Intermediate', 'Advanced']
goals = ['Lose Weight', 'Build Muscle', 'Increase Flexibility', 'General Fitness']

def get_user_input():
    print("Welcome to the Advanced Daily Workout Recommender!")
    
    user_name = input("Enter your name: ")
    preferred_workout_type = input(f"Choose your preferred workout type {list(workouts.keys())}: ")
    fitness_level = input(f"Select your fitness level {fitness_levels}: ")
    goal = input(f"Select your goal {goals}: ")
    
    cursor.execute("INSERT INTO users (name, fitness_level, goal) VALUES (?, ?, ?)", 
                   (user_name, fitness_level, goal))
    conn.commit()
    
    user_id = cursor.lastrowid
    
    return user_id, preferred_workout_type

def recommend_workout(user_id, preferred_workout_type):
    # Fetch user data
    cursor.execute("SELECT fitness_level, goal FROM users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()
    
    fitness_level, goal = user_data
    
    # Generate recommendations
    if feedback_based_model(user_id):
        recommended_workouts = feedback_based_model(user_id)
    else:
        recommended_workouts = random.sample(workouts[preferred_workout_type], 3)
    
    print("\nRecommended Workouts for You:")
    print(f"Fitness Level: {fitness_level}")
    print(f"Goal: {goal}")
    
    for workout in recommended_workouts:
        print(f"- {workout}")
    
    for workout in recommended_workouts:
        feedback = int(input(f"Rate the workout '{workout}' on a scale of 1-5: "))
        cursor.execute("INSERT INTO workouts (user_id, workout_type, workout_name, feedback) VALUES (?, ?, ?, ?)", 
                       (user_id, preferred_workout_type, workout, feedback))
    
    conn.commit()
    print("\nThank you for your feedback! We will tailor future recommendations accordingly.")

def feedback_based_model(user_id):
    cursor.execute("SELECT workout_name, feedback FROM workouts WHERE user_id=?", (user_id,))
    data = cursor.fetchall()
    
    if len(data) < 5:
        return None
    
    workout_names = []
    feedback_scores = []
    
    for workout_name, feedback in data:
        workout_names.append(workout_name)
        feedback_scores.append(feedback)
    
    # Convert workout names to numerical values
    workout_mapping = {name: i for i, name in enumerate(set(workout_names))}
    workout_ids = [workout_mapping[name] for name in workout_names]
    
    # Prepare training data
    X = np.array(workout_ids).reshape(-1, 1)
    y = np.array(feedback_scores)
    
    # Train KNN model
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(X, y)
    
    # Predict top 3 recommended workouts
    predictions = knn.predict(np.array(list(workout_mapping.values())).reshape(-1, 1))
    top_workouts = [name for name, score in sorted(zip(workout_mapping.keys(), predictions), key=lambda x: x[1], reverse=True)][:3]
    
    return top_workouts

def main():
    user_id, preferred_workout_type = get_user_input()
    recommend_workout(user_id, preferred_workout_type)
    print("\nGood luck with your workout!")

if __name__ == "__main__":
    main()
    conn.close()
