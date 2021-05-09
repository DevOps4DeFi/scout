# Badger Scout

Scout is an open-source version of the monitoring tool used by [Badger Finance](https://github.com/Badger-Finance) to watch simple ops metrics on our Ethereum smart contracts.  Over time, community dashboards will be added.

Scout inspects each block on the chain, creates Badger-relevant events, and uses Grafana with Prometheus the data source to store/display/work on them.

Included is a base set of UI-unchangeable dashboards configured by JSON that are used for alerting, and uses configuration as code wherever possible.  Additional dashboards can be added by the community by making a pull request to add the JSON file into the `grafana/dashboards` directory structure.  

Terraform code is currently in the root directory because it is required to pull modules. However, it may later be split into a different repo.  

All source code can be found in the `docker/` directory. The Badger-written Python collector can be found in `docker/scout`.

## Development Environment

The simplest way to get up and running is to run the below commands from this directory:

```bash
cd docker
export ETHNODEURL=https://ethnode.infra.example
export 
docker-compose build
docker-compose up
```

* Once running, access Grafana at localhost:3000, Prometheus at localhost:9090, Prometheus Scout target at localhost:8801.
* `docker-compose.yaml` contains environment variables to modify basic behavior.

## Production Environment

Look in the `terraform/` directory to figure out how to build this out in the cloud.  The module is meant to work with network and load balancer resources provided by the DevOps4DeFi [terraform-baseline](https://github.com/DevOps4DeFi/terraform-baseline) module.

More documentation is still required.

the `docker/build.sh` script is used to build the containers and push them to the Terraform ECR repos.

## Grafana Dashboards

Look in the `grafana/provisioning/datasources` directory to see the data source that is used to access Prometheus.  Note that it depends on an environment variable called `PROMETHEUS_URL`.

The dashboard structure is specified in the `grafana/dashboards` directory.  The same directory structure will be shown in Grafana.

To make changes to these dashboards add/edit/remove the JSON files in this directory and redeploy Grafana with `docker-compose restart`.  Dashboards can also be copied and edited in the Grafana console and exported as a JSON file to change/templatize.

Note that Grafana interpolates `${VAR}` as `VAR` environment variables from the YAML files in `grafana/provisioning/datasources`.
