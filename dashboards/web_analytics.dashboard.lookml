---
- dashboard: web_analytics
  title: Web Analytics
  preferred_viewer: dashboards
  layout: newspaper
  tabs:
  - name: ''
    label: ''
  elements:
  - title: Total Visitors
    name: Total Visitors
    model: "@{model_name}"
    explore: events
    type: single_value
    fields: [events.unique_visitors, events.event_week]
    filters:
      events.event_date: 2 weeks ago for 2 weeks
    sorts: [events.event_week desc]
    limit: 500
    column_limit: 50
    dynamic_fields:
    - table_calculation: change
      label: Change
      expression: "${events.unique_visitors}-offset(${events.unique_visitors},1)"
    query_timezone: America/Los_Angeles
    font_size: medium
    value_format: ''
    text_color: black
    colors: ["#1f78b4", "#a6cee3", "#33a02c", "#b2df8a", "#e31a1c", "#fb9a99", "#ff7f00",
      "#fdbf6f", "#6a3d9a", "#cab2d6", "#b15928", "#edbc0e"]
    show_single_value_title: true
    show_comparison: true
    comparison_type: change
    comparison_reverse_colors: false
    show_comparison_label: true
    comparison_label: Weekly Change
    single_value_title: Visitors Past Week
    note_state: collapsed
    note_display: below
    note_text: ''
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
    row: 0
    col: 0
    width: 8
    height: 3
    tab_name: ''
  - title: Total Converted Visitors
    name: Total Converted Visitors
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [users.count]
    sorts: [users.count desc]
    limit: 500
    font_size: medium
    text_color: black
    listen:
      Traffic Source: users.traffic_source
      Date: order_items.created_date
    row: 0
    col: 16
    width: 8
    height: 3
    tab_name: ''
  - title: Total Profit
    name: Total Profit
    model: "@{model_name}"
    explore: order_items
    type: single_value
    fields: [order_items.total_sale_price]
    sorts: [orders.total_profit_k desc, order_items.total_sale_price desc]
    limit: 500
    query_timezone: America/Los_Angeles
    font_size: medium
    value_format: "$#,###"
    text_color: black
    colors: ["#1f78b4", "#a6cee3", "#33a02c", "#b2df8a", "#e31a1c", "#fb9a99", "#ff7f00",
      "#fdbf6f", "#6a3d9a", "#cab2d6", "#b15928", "#edbc0e"]
    color_palette: Default
    note_state: expanded
    note_display: below
    note_text: ''
    listen:
      Traffic Source: users.traffic_source
      Date: order_items.created_date
    row: 0
    col: 8
    width: 8
    height: 3
    tab_name: ''
  - title: Visits by Browser
    name: Visits by Browser
    model: "@{model_name}"
    explore: events
    type: looker_pie
    fields: [events.browser, events.count]
    sorts: [events.count desc]
    limit: 50
    query_timezone: America/Los_Angeles
    show_null_labels: false
    value_labels: legend
    label_type: labPer
    show_view_names: true
    colors: ["#635189", "#8D7FB9", "#EA8A2F", "#e9b404", "#49cec1", "#a2dcf3", "#1ea8df",
      "#7F7977"]
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 25
    col: 0
    width: 12
    height: 8
    tab_name: ''
  - title: How Long do Visitors Spend on Website?
    name: How Long do Visitors Spend on Website?
    model: "@{model_name}"
    explore: events
    type: looker_bar
    fields: [sessions.duration_seconds_tier, sessions.count]
    sorts: [sessions.duration_seconds_tier]
    limit: 500
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_labels: [Number of Sessions]
    x_axis_gridlines: false
    show_x_axis_label: false
    show_x_axis_ticks: true
    x_axis_label: Session Duration in Seconds
    show_value_labels: false
    show_view_names: true
    show_null_labels: false
    stacking: normal
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    x_axis_scale: auto
    label_density: 25
    legend_position: center
    y_axis_combined: true
    ordering: none
    colors: ["#8D7FB9"]
    x_axis_label_rotation: -45
    show_dropoff: false
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 18
    col: 0
    width: 11
    height: 7
    tab_name: ''
  - title: Bounce Rate by Page
    name: Bounce Rate by Page
    model: "@{model_name}"
    explore: sessions
    type: looker_column
    fields: [events.event_type, events.bounce_rate, sessions.count]
    filters:
      events.event_type: -"Purchase",-"Login",-"Register",-"History",-"Cancel",-"Return"
      sessions.session_start_date: 7 days
    sorts: [sessions.count desc]
    limit: 10
    stacking: ''
    show_value_labels: false
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    x_axis_scale: auto
    y_axis_orientation: [left, right]
    series_types:
      events.bounce_rate: line
    y_axis_combined: false
    label_density: 10
    series_labels:
      events.bounce_rate: Bounce Rate by Page
      events.count: Number of Page Views
    legend_position: center
    colors: ["#a2dcf3", "#64518A", "#8D7FB9"]
    show_null_labels: false
    ordering: none
    show_null_points: true
    point_style: circle_outline
    interpolation: linear
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 10
    col: 12
    width: 12
    height: 8
    tab_name: ''
  - title: Most Popular Brands
    name: Most Popular Brands
    model: "@{model_name}"
    explore: events
    type: table
    fields: [product_viewed.brand, events.count, events.unique_visitors, sessions.count_purchase,
      sessions.cart_to_checkout_conversion]
    filters:
      product_viewed.brand: "-NULL"
    sorts: [events.count desc]
    limit: 10
    query_timezone: America/Los_Angeles
    show_view_names: false
    show_row_numbers: true
    show_value_labels: true
    show_null_labels: false
    stacking: ''
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    x_axis_scale: auto
    y_axis_combined: true
    series_labels:
      events.count: Total Pageviews
    y_axis_labels: [Total Pageviews]
    x_axis_label: Brand Name
    label_density: 25
    legend_position: center
    ordering: none
    colors: ["#64518A", "#8D7FB9"]
    hide_legend: false
    show_dropoff: false
    truncate_column_names: false
    table_theme: gray
    limit_displayed_rows: false
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 25
    col: 12
    width: 12
    height: 8
    tab_name: ''
  - title: eCommerce Funnel
    name: eCommerce Funnel
    model: "@{model_name}"
    explore: sessions
    type: looker_column
    fields: [sessions.all_sessions, sessions.count_browse_or_later, sessions.count_product_or_later,
      sessions.count_cart_or_later, sessions.count_purchase]
    filters:
      users.traffic_source: ''
    sorts: [sessions.all_sessions desc]
    limit: 500
    column_limit: 50
    query_timezone: America/Los_Angeles
    stacking: ''
    show_value_labels: true
    label_density: 25
    legend_position: center
    x_axis_gridlines: false
    y_axis_gridlines: false
    show_view_names: false
    limit_displayed_rows: false
    y_axis_combined: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    x_axis_scale: auto
    y_axis_scale_mode: linear
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    leftAxisLabelVisible: false
    leftAxisLabel: ''
    rightAxisLabelVisible: true
    rightAxisLabel: Sessions
    barColors: ["#5245ed", "#49cec1"]
    smoothedBars: true
    orientation: automatic
    labelPosition: left
    percentType: total
    percentPosition: inline
    valuePosition: right
    labelColorEnabled: false
    labelColor: "#FFF"
    colors: ["#5245ed", "#a2dcf3", "#776fdf", "#1ea8df", "#49cec1", "#776fdf", "#49cec1",
      "#1ea8df", "#a2dcf3", "#776fdf", "#776fdf", "#635189"]
    show_dropoff: true
    point_style: circle
    show_null_points: true
    interpolation: linear
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: sessions.session_start_date
    row: 3
    col: 10
    width: 14
    height: 7
    tab_name: ''
  - title: Global Events
    name: Global Events
    model: "@{model_name}"
    explore: events
    type: looker_map
    fields: [events.approx_location, events.count]
    sorts: [events.count desc]
    limit: 1000
    query_timezone: America/Los_Angeles
    show_view_names: true
    stacking: ''
    show_value_labels: false
    label_density: 25
    legend_position: center
    x_axis_gridlines: false
    y_axis_gridlines: true
    y_axis_combined: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    x_axis_scale: auto
    ordering: none
    show_null_labels: false
    loading: false
    map_plot_mode: points
    heatmap_gridlines: true
    map_tile_provider: positron
    map_position: fit_data
    map_scale_indicator: 'off'
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: pixels
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_legend: true
    quantize_map_value_colors: false
    map: world
    map_projection: ''
    quantize_colors: false
    colors: [whitesmoke, "#64518A"]
    outer_border_color: grey
    inner_border_color: lightgrey
    map_pannable: true
    map_zoomable: true
    map_marker_color: ["#1ea8df"]
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 10
    col: 0
    width: 12
    height: 8
    tab_name: ''
  - title: Daily Session and User Count
    name: Daily Session and User Count
    model: "@{model_name}"
    explore: sessions
    type: looker_line
    fields: [sessions.session_start_date, sessions.count, sessions.overall_conversion]
    filters:
      sessions.session_start_date: 7 days
    sorts: [sessions.session_start_date]
    limit: 500
    column_limit: 50
    query_timezone: America/Los_Angeles
    show_view_names: false
    stacking: ''
    show_value_labels: false
    label_density: 25
    legend_position: center
    x_axis_gridlines: false
    y_axis_gridlines: true
    y_axis_combined: false
    show_y_axis_labels: false
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: false
    show_x_axis_ticks: true
    x_axis_scale: auto
    colors: ["#5245ed", "#1ea8df", "#353b49", "#49cec1", "#b3a0dd", "#db7f2a", "#706080",
      "#a2dcf3", "#776fdf", "#e9b404", "#635189"]
    show_row_numbers: true
    point_style: circle_outline
    interpolation: linear
    discontinuous_nulls: false
    show_null_points: true
    ordering: none
    show_null_labels: false
    y_axis_orientation: [left, right]
    hide_legend: false
    limit_displayed_rows: false
    y_axis_scale_mode: linear
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 18
    col: 11
    width: 13
    height: 7
    tab_name: ''
  - title: Percent Purchasing Sessions
    name: Percent Purchasing Sessions
    model: "@{model_name}"
    explore: sessions
    type: looker_pie
    fields: [sessions.includes_purchase, sessions.count]
    filters:
      sessions.session_start_date: 7 days
    sorts: [sessions.all_sessions desc, sessions.includes_purchase]
    limit: 500
    column_limit: 50
    query_timezone: America/Los_Angeles
    show_view_names: true
    colors: ["#5245ed", "#a2dcf3"]
    show_row_numbers: true
    ordering: none
    show_null_labels: false
    value_labels: legend
    label_type: labPer
    stacking: normal
    show_value_labels: false
    label_density: 25
    legend_position: center
    x_axis_gridlines: false
    y_axis_gridlines: true
    y_axis_combined: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    x_axis_scale: ordinal
    point_style: circle_outline
    interpolation: linear
    discontinuous_nulls: false
    show_null_points: true
    inner_radius: 50
    series_labels:
      'No': No Purchase
      'Yes': Results in Purchase
    series_colors: {}
    note_state: collapsed
    note_display: below
    note_text: Percent of unique visits that result in a purchase
    listen:
      Browser: events.browser
      Traffic Source: users.traffic_source
      Date: events.event_date
    row: 3
    col: 0
    width: 10
    height: 7
    tab_name: ''
  filters:
  - name: Browser
    title: Browser
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: advanced
      display: popover
    model: "@{model_name}"
    explore: events
    listens_to_filters: []
    field: events.browser
  - name: Traffic Source
    title: Traffic Source
    type: field_filter
    default_value:
    allow_multiple_values: true
    required: false
    ui_config:
      type: advanced
      display: popover
    model: "@{model_name}"
    explore: events
    listens_to_filters: []
    field: users.traffic_source
  - name: Date
    title: Date
    type: date_filter
    default_value: 7 days
    allow_multiple_values: true
    required: false
    ui_config:
      type: advanced
      display: popover
