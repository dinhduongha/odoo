/* global QRCode */

import { session } from "@web/session";
import { getDataURLFromFile } from "@web/core/utils/urls";
import { deserializeDateTime } from "@web/core/l10n/dates";
/*
 * comes from o_spreadsheet.js
 * https://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript
 * */
export function uuidv4() {
    // mainly for jest and other browsers that do not have the crypto functionality
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        const r = (Math.random() * 16) | 0,
            v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

/**
 * Client-side uuidv7 generator (48-bit ms timestamp + random), matching the
 * server's uuidv7 primary keys. Time-ordered, so ids mint in chronological order.
 * Used for every internally-generated uuid in the POS.
 *
 * @returns {string}
 */
export function uuidv7() {
    const ts = Date.now();
    const b = crypto.getRandomValues(new Uint8Array(16));
    b[0] = Math.floor(ts / 2 ** 40) & 0xff;
    b[1] = Math.floor(ts / 2 ** 32) & 0xff;
    b[2] = Math.floor(ts / 2 ** 24) & 0xff;
    b[3] = Math.floor(ts / 2 ** 16) & 0xff;
    b[4] = Math.floor(ts / 2 ** 8) & 0xff;
    b[5] = ts & 0xff;
    b[6] = (b[6] & 0x0f) | 0x70; // version 7
    b[8] = (b[8] & 0x3f) | 0x80; // variant 10
    const h = [...b].map((x) => x.toString(16).padStart(2, "0"));
    return `${h[0]}${h[1]}${h[2]}${h[3]}-${h[4]}${h[5]}-${h[6]}${h[7]}-${h[8]}${h[9]}-${h[10]}${h[11]}${h[12]}${h[13]}${h[14]}${h[15]}`;
}

/**
 * uuid-safe id comparator (ascending). uuidv7 ids are time-ordered, so
 * lexicographic string order == chronological order. Coerces to string so
 * mixed/undefined ids never yield NaN. POS-local so it works in every POS
 * bundle (backend, kiosk, mobile) without depending on @mail.
 *
 * @returns {number} -1 if a < b, 1 if a > b, 0 if equal.
 */
export function compareId(a, b) {
    const sa = a == null ? "" : String(a);
    const sb = b == null ? "" : String(b);
    return sa === sb ? 0 : sa < sb ? -1 : 1;
}

/**
 * Tell whether an id belongs to a server-persisted record (as opposed to a
 * record that only exists locally in the POS).
 *
 * Before the int->uuid PK migration this was simply `typeof id === "number"`
 * (server ids were positive integers, local temps were negatives). Now every
 * PK is a uuid string, so both cases look alike. The one invariant that still
 * holds: a locally-created record gets a client-generated `uuidv4()` id (version
 * nibble "4" at index 14), whereas any server record — a uuidv7 PK or a seeded
 * low-uuid like `00000000-0000-0000-0000-000000000001` — is not a uuidv4.
 * So "not a local uuidv4" == server id. Legacy numeric ids stay supported.
 */
export function isServerId(id) {
    if (!id) {
        return false;
    }
    if (typeof id === "number") {
        return id >= 0;
    }
    return !(typeof id === "string" && id[14] === "4");
}

/**
 * Formats the given `url` with correct protocol and port.
 * Useful for communicating to local iot box instance.
 * @param {string} url
 * @returns {string}
 */
export function deduceUrl(url) {
    const protocol = odoo.use_lna ? "http:" : window.location.protocol;
    if (!url.includes("//")) {
        url = `${protocol}//${url}`;
    }
    if (url.indexOf(":", 6) < 0) {
        url += ":" + (protocol === "https:" ? 443 : 8069);
    }
    return url;
}

export function constructAttributeString(line) {
    let attributeString = "";

    if (line.attribute_value_ids && line.attribute_value_ids.length > 0) {
        for (const value of line.attribute_value_ids) {
            if (value.is_custom) {
                const customValue = line.custom_attribute_value_ids.find(
                    (cus) =>
                        String(cus.custom_product_template_attribute_value_id?.id) === String(value.id) // uuid: compare ptav ids as strings
                );
                if (customValue) {
                    attributeString += `${value.attribute_id.name}: ${value.name}: ${customValue.custom_value}, `;
                }
            } else {
                attributeString += `${value.name}, `;
            }
        }

        attributeString = attributeString.slice(0, -2);
    } else if (
        attributeString === "" &&
        line?.product_id?.product_template_variant_value_ids?.length > 0
    ) {
        attributeString = line.product_id.product_template_variant_value_ids
            ?.map((attr) => attr.name)
            .join(", ");
    }

    return attributeString;
}

export function constructFullProductName(line) {
    const attributeString = constructAttributeString(line);
    return attributeString
        ? `${line?.product_id?.name} (${attributeString})`
        : `${line?.product_id?.name}`;
}
/**
 * Returns a random 5 digits alphanumeric code
 * @returns {string}
 */
export function random5Chars() {
    let code = "";
    while (code.length != 5) {
        code = Math.random().toString(36).slice(2, 7);
    }
    return code;
}

export function qrCodeSrc(url, { size = 200 } = {}) {
    return `/report/barcode/QR/${encodeURIComponent(url)}?width=${size}&height=${size}`;
}

/**
 * @template T
 * @param {T[]} entries - The array of objects to search through.
 * @param {Function} [criterion=(x) => x] - A function that returns a number for each entry. The entry with the highest value of this function will be returned. If not provided, defaults to an identity function that returns the entry itself.
 * @param {boolean} [inverted=false] - If true, the entry with the lowest value of the criterion function will be returned instead.
 * @returns {T} The entry with the highest or lowest value of the criterion function, depending on the value of `inverted`.
 */
export function getMax(entries, { criterion = (x) => x, inverted = false } = {}) {
    return entries.reduce((prev, current) => {
        const res = criterion(prev) > criterion(current);
        return (inverted ? !res : res) ? prev : current;
    });
}
export function getMin(entries, options) {
    return getMax(entries, { ...options, inverted: true });
}
export function getOnNotified(bus, channel) {
    bus.addChannel(channel);
    return (notif, callback) => bus.subscribe(`${channel}-${notif}`, callback);
}

/**
 * Loading image is converted to a Promise to allow await when
 * loading an image. It resolves to the loaded image if successful,
 * else, resolves to false.
 *
 * [Source](https://stackoverflow.com/questions/45788934/how-to-turn-this-callback-into-a-promise-using-async-await)
 */
export function loadImage(url, options = {}) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.addEventListener("load", () => resolve(img));
        img.addEventListener("error", () => {
            if (options.onError) {
                options.onError();
            }
            reject(new Error(`Failed to load image at ${url}`));
        });
        img.src = url;
    });
}

/**
 * Load all images in the given element.
 * @param {HTMLElement} el
 */

export function waitImages(containerElement, timeoutMs = 3000) {
    return new Promise((resolve) => {
        const images = containerElement.querySelectorAll("img");
        const total = images.length;
        let loadedCount = 0;
        let timedOut = false;

        if (total === 0) {
            resolve({ timedOut: false });
            return;
        }

        const timeoutId = setTimeout(() => {
            timedOut = true;
            resolve({ timedOut: true });
        }, timeoutMs);

        const onLoadOrError = () => {
            loadedCount++;
            if (loadedCount === total && !timedOut) {
                clearTimeout(timeoutId);
                resolve({ timedOut: false });
            }
        };

        images.forEach((img) => {
            if (img.complete) {
                onLoadOrError();
            } else {
                img.addEventListener("load", onLoadOrError);
                img.addEventListener("error", onLoadOrError);
            }
        });
    });
}

export class Counter {
    constructor(start = 0) {
        this.value = start;
    }
    next() {
        this.value++;
        return this.value;
    }
}

export function isValidPhone(string) {
    const phone = string.replace(/[\s.\-()]/g, "");
    const pattern = /^\+\d{8,18}$/;
    return pattern.test(phone);
}

export function isValidEmail(email) {
    return email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Checks whether an ip address is on the local network. So one of the ranges:
// 10.0.0.0 - 10.255.255.255
// 127.0.0.0 - 127.255.255.255
// 172.16.0.0 - 172.31.255.255
// 169.254.0.0 - 169.254.255.255
// 192.168.0.0 - 192.168.255.255
export function isPrivateIp(ip) {
    if (!ip || typeof ip !== "string") {
        return false;
    }
    const blocks = ip.split(".");
    if (blocks.length !== 4) {
        return false;
    }

    const [a, b, c, d] = blocks.map(Number);
    const invalidBlock = blocks.some(
        (b, i) => isNaN([a, b, c, d][i]) || [a, b, c, d][i] < 0 || [a, b, c, d][i] > 255
    );

    if (invalidBlock) {
        return false;
    }

    return (
        a === 10 ||
        a === 127 ||
        (a === 172 && b >= 16 && b <= 31) ||
        (a === 192 && b === 168) ||
        (a === 169 && b === 254)
    );
}

export const LONG_PRESS_DURATION = session.test_mode ? 100 : 500;

export async function getImageDataUrl(imageUrl) {
    const res = await fetch(imageUrl);
    const blob = await res.blob();
    return await getDataURLFromFile(blob);
}

export function orderUsageUTCtoLocalUtil(data) {
    const result = {};
    for (const [datetime, usage] of Object.entries(data)) {
        const dt = deserializeDateTime(datetime);
        const formattedDt = dt.toFormat("yyyy-MM-dd HH:mm:ss");
        result[formattedDt] = usage;
    }
    return result;
}

/**
 * Generates a QR code as a data URL in SVG format for a given URL.
 *
 * @param {string} url - The URL or text to encode in the QR code.
 * @param {Object} [options={}] - Optional configuration for the QR code.
 * @param {number} [options.width=150] - The width of the QR code.
 * @param {number} [options.height=150] - The height of the QR code.
 * @param {number} [options.correctLevel=QRCode.CorrectLevel.L] - The error correction level for the QR code.
 * @param {boolean} [options.useSVG=true] - Whether to generate the QR code as SVG.
 * @param {Object} [options.rest] - Additional options to pass to the QRCode constructor.
 * @returns {string} The QR code as a data URL in SVG format.
 */
export function generateQRCodeDataUrl(
    url,
    { width = 150, height = 150, correctLevel = QRCode.CorrectLevel.L, ...rest } = {}
) {
    const tempDiv = document.createElement("div");
    const options = { width, height, correctLevel, ...rest };

    new QRCode(tempDiv, { text: url, useSVG: true, ...options });

    const svg = tempDiv.querySelector("svg");
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);

    const qr_code_svg = new XMLSerializer().serializeToString(svg);
    return "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
}
