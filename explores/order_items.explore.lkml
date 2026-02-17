include: "/views/order_items.view.lkml"
include: "/views/users.view.lkml"
include: "/views/products.view.lkml"

explore: order_items {
  label: "Order Items"
  description: "Explore de pedidos con usuarios y productos"

  join: users {
    type: left_outer
    relationship: many_to_one
    sql_on: ${order_items.user_id} = ${users.id} ;;
  }

  join: products {
    type: left_outer
    relationship: many_to_one
    sql_on: ${order_items.product_id} = ${products.id} ;;
  }
}
