Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :articles
      resources :profiles, only: [:show]
      resources :users, only: [:create]
      post '/users/login', to: 'users#login'
      get '/user', to: 'users#show'
      put '/user', to: 'users#update'
    end
  end
end
