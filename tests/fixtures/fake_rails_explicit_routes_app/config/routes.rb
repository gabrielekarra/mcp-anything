# frozen_string_literal: true

Rails.application.routes.draw do
  # Standard resources
  resources :users
  resources :products, only: [:index, :show, :create]

  # Explicit to: syntax
  get '/status', to: 'health#show'
  post '/auth/login', to: 'sessions#create'

  # Hash-rocket syntax (used in Rails 3+ apps and engine routes)
  get '/legacy/items' => 'items#index'
  delete '/legacy/items/:id' => 'items#destroy'

  # Namespaced
  namespace :api do
    resources :orders
  end
end
