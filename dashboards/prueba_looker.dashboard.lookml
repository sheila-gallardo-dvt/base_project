---
- dashboard: prueba_looker
  title: Prueba Looker
  preferred_viewer: dashboards-next
  description: ''
  layout: newspaper
  tabs:
  - name: ''
    label: ''
  elements:
  - title: Untitled
    name: Untitled
    model: "@{model_name}"
    explore: order_items
    type: looker_line
    fields: [order_items.created_date, order_items.average_days_to_process]
    fill_fields: [order_items.created_date]
    filters:
      order_items.date_filter_type: interanual
    sorts: [order_items.created_date desc]
    limit: 500
    column_limit: 50
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
      Date Filter Type: order_items.date_filter_type
      Fecha: order_items.date_param
      Status: order_items.status
    row: 0
    col: 0
    width: 24
    height: 9
    tab_name: ''
  - title: Untitled
    name: Untitled (2)
    model: "@{model_name}"
    explore: order_items
    type: looker_column
    fields: [order_items.status, order_items.average_gross_margin]
    filters:
      order_items.date_param: 2025/01/16
      order_items.date_filter_type: interanual
    sorts: [order_items.average_gross_margin desc 0]
    limit: 500
    column_limit: 50
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
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    listen:
      Date Filter Type: order_items.date_filter_type
      Fecha: order_items.date_param
      Status: order_items.status
    row: 9
    col: 0
    width: 16
    height: 6
    tab_name: ''
  filters:
  - name: Date Filter Type
    title: Date Filter Type
    type: field_filter
    default_value: mensual
    allow_multiple_values: true
    required: true
    ui_config:
      type: dropdown_menu
      display: inline
    model: "@{model_name}"
    explore: order_items
    listens_to_filters: []
    field: order_items.date_filter_type
  - name: Fecha
    title: Fecha
    type: field_filter
    default_value: 2025/01/16
    allow_multiple_values: true
    required: false
    ui_config:
      type: advanced
      display: popover
      options: []
    model: "@{model_name}"
    explore: order_items
    listens_to_filters: []
    field: order_items.date_param
  - name: Status
    title: Status
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: checkboxes
      display: popover
    model: "@{model_name}"
    explore: order_items
    listens_to_filters: []
    field: order_items.status
