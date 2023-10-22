import xml.etree.ElementTree as ET

def merge_ts_files(primary_ts, secondary_ts, output_ts):
    # Parse the XML files
    tree1 = ET.parse(primary_ts)
    root1 = tree1.getroot()

    tree2 = ET.parse(secondary_ts)
    root2 = tree2.getroot()

    # Collect all the source tags in primary_ts for quick checking
    primary_sources = {message.find('source').text: message for message in root1.findall('.//message')}

    for message in root2.findall('.//message'):
        source_text = message.find('source').text
        # If the message source from secondary_ts exists in primary_ts, update its translation
        if source_text in primary_sources:
            old_translation = primary_sources[source_text].find('translation')
            new_translation = message.find('translation')
            if old_translation is not None and new_translation is not None:
                old_translation.text = new_translation.text
        # Otherwise, add the new message
        else:
            root1.append(message)

    # Save the merged file using UTF-8 encoding
    with open(output_ts, 'wb') as f:
        f.write(ET.tostring(root1, encoding='utf-8'))



# Usage
primary_file = 'langs.zh_CN.blank.ts'
secondary_file = 'langs.zh_CN.ts'
output_file = 'test.ts'
merge_ts_files(primary_file, secondary_file, output_file)
