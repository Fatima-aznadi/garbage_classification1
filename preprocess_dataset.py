import tensorflow as tf
import os

# Configuration
DATASET_DIR = "dataset_final"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SPLIT_RATIO = 0.2  # 20% pour le test/validation, 80% pour l'entraînement

print("="*50)
print("ÉTAPE 1 : CHARGEMENT ET SPLIT (80% Train / 20% Val)")
print("="*50)

# On charge les images ET on les sépare directement (Split)
# image_dataset_from_directory fait le resize automatiquement, 
# mais on va le refaire explicitement dans la fonction d'après pour respecter ta consigne.
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=SPLIT_RATIO,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=SPLIT_RATIO,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names
print(f"\nClasses détectées : {class_names}")
print(f"Nombre de lots (batches) d'entraînement : {len(train_ds)}")
print(f"Nombre de lots (batches) de validation : {len(val_ds)}\n")


print("="*50)
print("ÉTAPE 2 : PRÉTRAITEMENT EXPLICITE")
print("-> Resize (224x224) -> Augmentation -> Normalisation (0-1)")
print("="*50)

# Fonction de prétraitement pour l'ENTRAÎNEMENT (Avec Augmentation)
def preprocess_train(image, label):
    # 1. Resize explicite (Redimensionnement)
    image = tf.image.resize(image, [224, 224])
    
    # On convertit en float32 pour pouvoir faire des calculs dessus
    image = tf.cast(image, tf.float32)
    
    # 2. Data Augmentation (Flip et Rotation)
    image = tf.image.random_flip_left_right(image) # Miroir horizontal
    image = tf.image.random_rotation(image, 0.1)   # Rotation aléatoire de 10%
    
    # 3. Normalisation (0 à 1)
    image = image / 255.0
    
    return image, label

# Fonction de prétraitement pour la VALIDATION (SANS Augmentation)
# (Il ne faut JAMAIS augmenter les données de validation, on ne fait que resize et normaliser)
def preprocess_val(image, label):
    # 1. Resize explicite
    image = tf.image.resize(image, [224, 224])
    
    # 2. Normalisation (0 à 1)
    image = tf.cast(image, tf.float32) / 255.0
    
    return image, label

# On applique ces fonctions à nos datasets avec .map()
print("Application du preprocessing sur le jeu d'entraînement...")
train_ds = train_ds.map(preprocess_train, num_parallel_calls=tf.data.AUTOTUNE)

print("Application du preprocessing sur le jeu de validation...")
val_ds = val_ds.map(preprocess_val, num_parallel_calls=tf.data.AUTOTUNE)

# Optimisation pour que ça tourne vite sur le CPU
train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)


print("\n" + "="*50)
print("SUCCÈS ! Le preprocessing est terminé.")
print("Tes données sont prêtes à être utilisées pour l'entraînement.")
print("="*50)

# --- Petit test pour te prouver que ça marche ---
print("\nVérification d'un batch d'images...")
for images, labels in train_ds.take(1):
    print(f" - Forme des images dans le batch : {images.shape}") # Doit être (32, 224, 224, 3)
    print(f" - Valeur minimale des pixels : {tf.reduce_min(images).numpy():.2f}") # Doit être 0.00
    print(f" - Valeur maximale des pixels : {tf.reduce_max(images).numpy():.2f}") # Doit être 1.00
    print(" -> Normalisation 0-1 confirmée !")