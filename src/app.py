import boto3

def success() -> dict:
  """Lambda success response
  """
  return {
      "statusCode": 200,
      "body": "SUCCESS"
  }

def error() -> dict:
  """Lambda error response
  """
  return {
      "statusCode": 500,
      "body": "ERROR"
  }

def init_client():
  """Init AWS client object.
  """
  global client
  client = boto3.client('eks')

def scale_down_cluster(cluster_name:str = "") -> None:
  """Scale down to 0 the cluster identified by cluster_name.
  """
  global client

  # Looking for all cluster nodegroups
  print(f'Scaling down cluster {cluster_name}')
  ng_list = client.list_nodegroups(clusterName=cluster_name)["nodegroups"]

  # Scale them down
  for ng_id in ng_list:
    print(f'Scaling down node group {ng_id}')
    response = client.update_nodegroup_config(
      clusterName=cluster_name,
      nodegroupName=ng_id,
      scalingConfig={ 'desiredSize': 0 }
    )

def scale_down_clusters(cluster_names:list = []) -> bool:
  """Scale down to 0 the clusters identified by cluster names.
  """
  ret = True
  try:
    for cluster_name in cluster_names:
      scale_down_cluster(cluster_name)

  except Exception as e:
    print(f'Cluster {cluster_name} could not be scaled down : {e}')
    ret = False

  return ret

def get_eks_clusters() -> list:
  """Looking clusters concerned by the scale down, meaning looking
     for cluster with tag "soloio:autoscaledown" set to true
  """
  ret = []

  global client
  c = client.list_clusters()
  
  for cluster_name in c["clusters"]:
    cluster = client.describe_cluster(name=cluster_name)["cluster"]
    if "soloio:autoscaledown" in cluster["tags"] and cluster["tags"]["soloio:autoscaledown"] == "true":
      ret.append(cluster_name)

  return ret

def lambda_handler(event, context):
  # Init AWS client
  init_client()

  # Getting all clusters
  clusters_to_stop = get_eks_clusters()
  print(clusters_to_stop)

  # Launching the scale down
  if scale_down_clusters(clusters_to_stop):
    return success()
  else:
    return error()
