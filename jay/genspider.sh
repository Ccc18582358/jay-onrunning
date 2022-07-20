echo "Enter project name: "
read -r project_name
rm -rf templates/result/*
mkdir -p templates/result
mkdir -p templates/project/module/spiders
mkdir -p templates/project/module/items
mkdir -p templates/project/module/adapters
mkdir -p templates/project/module/downloadermiddlewares
scrapy startproject -s TEMPLATES_DIR='templates' "$project_name" templates/result

# 因为无法自动生成spider,所以借用middleware去生成
cd templates/result/"$project_name" || exit
mv items.py items/__init__.py
mv middlewares.py spiders/"$project_name"_spider.py
mv pipelines.py adapters/__init__.py






