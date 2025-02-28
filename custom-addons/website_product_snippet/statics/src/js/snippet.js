/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
import publicWidget from "@web/legacy/js/public/public_widget";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";

const ProductShowcase = publicWidget.Widget.extend({
    selector: '.product-showcase-snippet',
    
    start() {
        this._loadProducts();
        return this._super(...arguments);
    },

    async _loadProducts() {
        try {
            const data = await jsonrpc('/snippet/products');
            const container = this.el.querySelector('#productContainer');
            if (container) {
                container.innerHTML = '';
                
                data.products.forEach(product => {
                    const card = this._createProductCard(product);
                    container.insertAdjacentHTML('beforeend', card);
                });
            }
        } catch (error) {
            console.error('Failed to load products:', error);
        }
    },

    _createProductCard(product) {
        return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="product-card">
                    <div class="product-image">
                        <img src="${product.image_url}" alt="${product.name}"/>
                        <div class="product-overlay">
                            <h3>${product.name}</h3>
                            <p>${product.description || ''}</p>
                            <a href="${product.public_url}" class="btn btn-primary">
                                ${_t("Learn More")}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
});

registry.category("public_widgets").add("product-showcase", ProductShowcase);

// Snippet Options
const snippetOptions = {
    selector: '.product-showcase-snippet',

    async start() {
        await this._super(...arguments);
        const refreshButton = this.el.querySelector('.refresh-products');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this._refreshProducts());
        }
    },

    async _refreshProducts() {
        const widget = new ProductShowcase();
        await widget.attachTo(this.el);
    },
};

registry.category("snippet_options").add("product_showcase_options", snippetOptions);

export default {
    ProductShowcase,
    snippetOptions,
};