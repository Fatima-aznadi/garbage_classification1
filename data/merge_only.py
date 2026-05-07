import os
import shutil

sources = ["dataset1", "dataset2"]
output = "dataset_final"

classes = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# créer dossiers finaux
for c in classes:
    os.makedirs(f"{output}/{c}", exist_ok=True)

for source in sources:
    for c in classes:
        path = os.path.join(source, c)

        if os.path.exists(path):
            for img in os.listdir(path):
                src_img = os.path.join(path, img)
                dst_img = os.path.join(output, c, f"{source}_{img}")

                shutil.copy(src_img, dst_img)

print("Fusion terminée ✔ dataset_final prêt")