
def find_items_by_list(item_ids: list, items_list: list, id_key):

    output = []

    if len(item_ids) > 0:
        for item in items_list:
            if item[id_key] in item_ids:
                output.append(item)

    return output

