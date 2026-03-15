Rails.application.routes.draw do
  namespace :api do
    resources :users
    resources :posts, only: [:index, :show, :create]
    get '/health', to: 'status#health'
  end
end
