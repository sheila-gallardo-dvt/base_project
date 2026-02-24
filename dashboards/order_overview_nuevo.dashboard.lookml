---
- dashboard: order_overview_nuevo
  title: Order Overview nuevo
  preferred_viewer: dashboards-next
  description: Dashboard resumen de pedidos
  theme_name: ''
  layout: newspaper
  tabs:
  - name: ''
    label: ''
  elements:
  - title: Total Revenue
    name: Total Revenue
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [order_items.total_revenue]
    limit: 500
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 0
    col: 0
    width: 6
    height: 12
    tab_name: ''
  - title: Total Orders
    name: Total Orders
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [order_items.count]
    limit: 500
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 0
    col: 6
    width: 6
    height: 4
    tab_name: ''
  - title: Average Sale Price
    name: Average Sale Price
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [order_items.average_sale_price]
    limit: 500
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 0
    col: 12
    width: 6
    height: 4
    tab_name: ''
  - title: Completed Orders
    name: Completed Orders
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [order_items.count_completed_orders]
    limit: 500
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen: {}
    row: 0
    col: 18
    width: 6
    height: 4
    tab_name: ''
  - title: Orders Over Time
    name: Orders Over Time
    model: "@{model_name}"
    explore: order_items
    type: looker_line
    fields: [order_items.created_month, order_items.count, order_items.total_sale_price]
    sorts: [order_items.created_month desc]
    limit: 24
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    defaults_version: 1
    listen:
      Status: order_items.status
      Date: order_items.created_date
    row: 4
    col: 12
    width: 12
    height: 8
    tab_name: ''
  - title: Top Products by Revenue
    name: Top Products by Revenue
    model: "@{model_name}"
    explore: order_items
    type: looker_grid
    fields: [products.name, products.brand, products.category, order_items.count,
      order_items.total_sale_price]
    sorts: [order_items.total_sale_price desc]
    limit: 15
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    listen:
      Status: order_items.status
      Date: order_items.created_date
    row: 12
    col: 0
    width: 24
    height: 8
    tab_name: ''
  filters:
  - name: Status
    title: Status
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: button_group
      display: inline
    model: "@{model_name}"
    explore: order_items
    listens_to_filters: []
    field: order_items.status
  - name: Date
    title: Date
    type: field_filter
    default_value: 12 months
    allow_multiple_values: true
    required: false
    ui_config:
      type: relative_timeframes
      display: inline
    model: "@{model_name}"
    explore: order_items
    listens_to_filters: []
    field: order_items.created_date
