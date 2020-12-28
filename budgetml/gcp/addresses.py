def create_static_ip_address(compute, project, region, static_ip):
    config = {
        'name': static_ip
    }

    return compute.addresses().insert(
        project=project,
        region=region,
        body=config).execute()
