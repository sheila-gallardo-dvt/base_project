project_name: "base_project"

# Constants exportables para que cada tenant los sobreescriba
constant: connection_name {
  value: "carlos-looker-training"
  export: override_required
}

constant: model_name {
  value: "base_project"
  export: override_required
}

constant: schema_name {
  value: "looker"
  export: override_required
}
