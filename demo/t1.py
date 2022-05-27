import re
output_dir = None
if output_dir is None:
    """
        Example: D:/t\\a/b.cn
    """
    sorted_paths = ['http://breath.cn\\t\\a/v/s\\d/b']
    img_file_path = sorted_paths[0]  # D:/t\\a/b.cn
    import os
    output_dir = os.path.dirname(img_file_path)
    file_name = os.path.basename(img_file_path)
    print(f'dir: {output_dir} file_name: {file_name}')
