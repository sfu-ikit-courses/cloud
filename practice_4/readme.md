# Инструкция к выполнению практики

## 1. Тегирование и пуш Docker-образа в свой репозиторий
```bash
docker tag server <username>/server
docker push <username>/server
```
*\<username\> - логин в Docker Hub*

## 2. Установка kubectl и minikube
*Установка на macOS*
```bash
brew install kubectl
brew install minikube
```

## 3. Проверка версий
```bash
kubectl version --client
minikube version
```

## 4. Старт Minikube
```bash
minikube start
```

## 5. Применение конфигурации Kubernetes
```bash
kubectl apply -f k8s.yaml
```

## 6. Проверка подов и сервисов
```bash
kubectl get pods
kubectl get svc
```

## 7. Доступ к кластеру на локальном хосте
```bash
minikube service server-svc
```

## 8. Интерактивный доступ к поду
```bash
kubectl exec -it $(kubectl get pods --no-headers -o custom-columns=":metadata.name" | awk 'NR==1') -- sh
```

## 9. Остановка Minikube
```bash
minikube stop
```

## 10. Полное удаление Minikube
```bash
minikube delete
```
