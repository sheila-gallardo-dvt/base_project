connection: "@{connection_name}"

include: "/views/*.view.lkml"
include: "/explores/*.explore.lkml"
include: "/dashboards/*.dashboard.lookml"

datagroup: base_project_datagroup {
  max_cache_age: "1 hour"
}

persist_with: base_project_datagroup
