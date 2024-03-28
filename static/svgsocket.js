
import { WebSocketModule } from '/static/star_ray/websocket.js';

const SVGSocketModule = (function () {

    const svg_parser = new DOMParser();
    // perhaps we need access to this to add new namespaces?
    const namespace_resolver = (prefix) => {
        const ns = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink',
        };
        return ns[prefix] || null;
    };
    // server message callback
    WebSocketModule.onMessage(function (event) {
        let data;
        try {
            data = JSON.parse(event);
        } catch (error) {
            const message = {
                statusCode: 400,
                errorMessage: "JSON parse error: " + error.message
            };
            console.error(message.errorMessage);
            const json_message = JSON.stringify(message);
            WebSocketModule.send(json_message);
            return
        }
        // TODO catch any exceptions here
        console.log(data.xpath, data.attributes)
        updateSvg(data.xpath, data.attributes)
    });


    // Function to update SVG based on XPath and attributes
    function updateSvg(xpath, attributes) {
        // Namespace resolver - adjust as needed for other namespaces
        // TODO name spaces need to be set by the server!
        const svg_container = document.getElementById('svg-container');
        // const svg_root = document.getElementById("root")
        // if (svg_elements.length != 1) {
        //     console.error("svg-container contains multiple <svg/> elements.")
        //     return
        // }

        // const svg_root = svg_elements[0]
        // Evaluate XPath and get all matching elements as a snapshot
        const result = document.evaluate(xpath, svg_container, namespace_resolver, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);

        if (result.snapshotLength == 0) {
            console.error(`no elements were found from xpath query: ${xpath}`)
            return
        }

        // Iterate over each node in the snapshot
        for (let i = 0; i < result.snapshotLength; i++) {
            const element = result.snapshotItem(i);
            updateElement(element, attributes, namespace_resolver)
        }
    }

    function updateElement(element, attributes, namespace_resolver) {
        // If attributes is a string, replace the selected element or its content
        if (typeof attributes === 'string') {
            if (element.nodeType === Node.ELEMENT_NODE) {
                const namespaceDeclarations = Object.entries(namespace_resolver)
                    .map(([prefix, uri]) => `xmlns:${prefix}="${uri}"`)
                    .join(' ');
                var svgString = `<svg ${namespaceDeclarations}>${attributes}</svg>`;
                // Parse the attributes string as XML using the global DOMParser
                var doc = svg_parser.parseFromString(svgString, 'application/xml');
                var newNode = document.importNode(doc.documentElement.firstChild, true);
                element.parentNode.replaceChild(newNode, element);
            } else if (element.nodeType === Node.TEXT_NODE) {
                // Replace the text node value
                element.nodeValue = attributes;
            }
        } else if (typeof attributes === 'object') {
            // Iterate over each attribute and update
            for (const [attr, value] of Object.entries(attributes)) {
                element.setAttribute(attr, value);
            }
        } else {
            throw new Error("Attributes must be either a string or an object.");
        }

    }
    return { namespace_resolver };
})();

export { SVGSocketModule };




